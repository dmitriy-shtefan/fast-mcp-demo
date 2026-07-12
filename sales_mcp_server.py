"""
FastMCP demo: sales analytics from a local CSV file.

What this demonstrates:
- MCP tools as small typed Python functions.
- Read-only access to business data.
- Resources for static context.
- A reusable prompt for an AI sales analyst.

Setup:
    pip install fastmcp

Run as an MCP server:
    python3 sales_mcp_server.py

Run local preview without an MCP host:
    python3 sales_mcp_server.py --demo
"""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = "sales_data.csv"
mcp = FastMCP("SalesAnalyticsMCP")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """Unauthenticated readiness endpoint for hosted deployments."""
    return JSONResponse({"status": "ok", "service": "sales-analytics-mcp"})


def safe_csv_path(file_name: str) -> Path:
    """Allow reading only CSV files inside this demo directory."""
    if not file_name or Path(file_name).is_absolute():
        raise ValueError("file_name must be a relative CSV file name")

    candidate = (BASE_DIR / file_name).resolve()
    if BASE_DIR not in candidate.parents and candidate != BASE_DIR:
        raise ValueError("file_name must stay inside the demo directory")
    if candidate.suffix.lower() != ".csv":
        raise ValueError("Only .csv files are allowed")
    if not candidate.exists():
        raise FileNotFoundError(f"CSV file not found: {file_name}")

    return candidate


def money(value: float) -> float:
    return round(value, 2)


def percent(value: float) -> float:
    return round(value * 100, 2)


def load_rows(file_name: str = DEFAULT_CSV) -> list[dict[str, Any]]:
    csv_path = safe_csv_path(file_name)
    rows: list[dict[str, Any]] = []

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        required_columns = {
            "order_id",
            "date",
            "region",
            "channel",
            "product",
            "category",
            "quantity",
            "unit_price",
            "cost_per_unit",
            "customer_segment",
        }
        missing_columns = required_columns.difference(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Missing CSV columns: {sorted(missing_columns)}")

        for raw in reader:
            quantity = int(raw["quantity"])
            unit_price = float(raw["unit_price"])
            cost_per_unit = float(raw["cost_per_unit"])
            revenue = quantity * unit_price
            gross_profit = quantity * (unit_price - cost_per_unit)

            rows.append(
                {
                    "order_id": raw["order_id"],
                    "date": date.fromisoformat(raw["date"]),
                    "region": raw["region"],
                    "channel": raw["channel"],
                    "product": raw["product"],
                    "category": raw["category"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "cost_per_unit": cost_per_unit,
                    "customer_segment": raw["customer_segment"],
                    "revenue": revenue,
                    "gross_profit": gross_profit,
                }
            )

    return rows


def group_sum(rows: list[dict[str, Any]], key: str, metric: str) -> dict[str, float]:
    grouped: dict[str, float] = defaultdict(float)
    for row in rows:
        grouped[str(row[key])] += float(row[metric])
    return dict(sorted(grouped.items(), key=lambda item: item[1], reverse=True))


@mcp.tool
def load_sales_summary(file_name: str = DEFAULT_CSV) -> dict[str, Any]:
    """
    Return high-level sales metrics from a local CSV file.

    The tool is read-only and accepts only CSV files from the demo directory.
    """
    rows = load_rows(file_name)
    if not rows:
        return {"file": file_name, "orders": 0, "message": "CSV file is empty"}

    total_revenue = sum(row["revenue"] for row in rows)
    total_profit = sum(row["gross_profit"] for row in rows)
    total_units = sum(row["quantity"] for row in rows)
    order_dates = [row["date"] for row in rows]

    return {
        "file": file_name,
        "period_start": min(order_dates).isoformat(),
        "period_end": max(order_dates).isoformat(),
        "orders": len(rows),
        "units_sold": total_units,
        "revenue_uah": money(total_revenue),
        "gross_profit_uah": money(total_profit),
        "gross_margin_pct": percent(total_profit / total_revenue) if total_revenue else 0,
        "average_order_value_uah": money(total_revenue / len(rows)),
        "unique_products": len({row["product"] for row in rows}),
        "revenue_by_region_uah": {key: money(value) for key, value in group_sum(rows, "region", "revenue").items()},
        "revenue_by_channel_uah": {key: money(value) for key, value in group_sum(rows, "channel", "revenue").items()},
    }


@mcp.tool
def top_products(
    file_name: str = DEFAULT_CSV,
    limit: int = 5,
    metric: Literal["revenue", "gross_profit", "quantity"] = "revenue",
) -> list[dict[str, Any]]:
    """
    Return top products by revenue, gross profit, or quantity.

    Use this when the business question is about best-performing products.
    """
    if limit < 1 or limit > 20:
        raise ValueError("limit must be between 1 and 20")

    rows = load_rows(file_name)
    product_stats: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in rows:
        product = row["product"]
        product_stats[product]["revenue"] += row["revenue"]
        product_stats[product]["gross_profit"] += row["gross_profit"]
        product_stats[product]["quantity"] += row["quantity"]
        product_stats[product]["orders"] += 1

    ranked = sorted(product_stats.items(), key=lambda item: item[1][metric], reverse=True)

    return [
        {
            "product": product,
            "orders": int(stats["orders"]),
            "quantity": int(stats["quantity"]),
            "revenue_uah": money(stats["revenue"]),
            "gross_profit_uah": money(stats["gross_profit"]),
            "gross_margin_pct": percent(stats["gross_profit"] / stats["revenue"]) if stats["revenue"] else 0,
        }
        for product, stats in ranked[:limit]
    ]


@mcp.tool
def monthly_sales_report(file_name: str = DEFAULT_CSV) -> list[dict[str, Any]]:
    """
    Return monthly sales dynamics for revenue, gross profit, and units sold.

    Use this when the agent needs to explain growth or decline over time.
    """
    rows = load_rows(file_name)
    monthly: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in rows:
        month = row["date"].strftime("%Y-%m")
        monthly[month]["orders"] += 1
        monthly[month]["quantity"] += row["quantity"]
        monthly[month]["revenue"] += row["revenue"]
        monthly[month]["gross_profit"] += row["gross_profit"]

    return [
        {
            "month": month,
            "orders": int(stats["orders"]),
            "units_sold": int(stats["quantity"]),
            "revenue_uah": money(stats["revenue"]),
            "gross_profit_uah": money(stats["gross_profit"]),
            "gross_margin_pct": percent(stats["gross_profit"] / stats["revenue"]) if stats["revenue"] else 0,
        }
        for month, stats in sorted(monthly.items())
    ]


@mcp.resource("sales://sample-csv")
def sample_csv_resource() -> str:
    """Return the sample CSV as read-only text context."""
    return safe_csv_path(DEFAULT_CSV).read_text(encoding="utf-8")


@mcp.resource("sales://business-questions")
def business_questions_resource() -> str:
    """Return example business questions for this sales dataset."""
    return "\n".join(
        [
            "1. Який загальний дохід і валовий прибуток за період?",
            "2. Які продукти дали найбільшу виручку?",
            "3. Які регіони і канали продажів найсильніші?",
            "4. Чи зростають продажі від місяця до місяця?",
            "5. Які 2-3 дії варто запропонувати бізнесу?",
        ]
    )


@mcp.prompt
def sales_report_prompt(company_context: str = "B2B SaaS компанія") -> str:
    """
    Prompt template for an AI sales analyst that uses the sales MCP tools.
    """
    return f"""
Ви - AI sales analyst для компанії: {company_context}.

Підготуйте короткий Markdown-звіт українською мовою:
1. Стислий executive summary на 2-3 речення.
2. Основні метрики: revenue, gross profit, margin, average order value.
3. Топ продуктів і найсильніші регіони/канали.
4. Динаміка по місяцях.
5. 2-3 практичні бізнес-рекомендації.

Використовуйте тільки факти, отримані з MCP tools або resources.
Не вигадуйте замовлення, продукти, суми або тренди.
""".strip()


def run_local_demo() -> None:
    print("\n=== Sales MCP local preview ===\n")
    print("Tool: load_sales_summary")
    print(json.dumps(load_sales_summary(), ensure_ascii=False, indent=2))

    print("\nTool: top_products(metric='revenue')")
    print(json.dumps(top_products(metric="revenue"), ensure_ascii=False, indent=2))

    print("\nTool: monthly_sales_report")
    print(json.dumps(monthly_sales_report(), ensure_ascii=False, indent=2))

    print("\nResource: sales://business-questions")
    print(business_questions_resource())

    print("\nPrompt: sales_report_prompt")
    print(sales_report_prompt())


def main() -> None:
    if "--demo" in sys.argv:
        run_local_demo()
    elif should_run_http():
        mcp.run(
            transport="http",
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
            stateless_http=True,
        )
    else:
        mcp.run()


def should_run_http() -> bool:
    transport = os.environ.get("MCP_TRANSPORT", "").lower()
    return "--http" in sys.argv or transport in {"http", "streamable-http"} or "PORT" in os.environ


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
