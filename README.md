# FastMCP demo: аналіз продажів із CSV

MCP Demo показує, як перетворити кілька Python-функцій для аналізу продажів на MCP tools/resources/prompts.

## Файли

- `sales_mcp_server.py` - FastMCP server.
- `sales_data.csv` - маленький приклад продажів за 3 місяці.

## Що демонструє приклад

- `tool: load_sales_summary` - рахує загальні метрики продажів.
- `tool: top_products` - повертає топ продуктів за виручкою, прибутком або кількістю.
- `tool: monthly_sales_report` - показує динаміку продажів по місяцях.
- `resource: sales://sample-csv` - дає read-only доступ до sample CSV.
- `resource: sales://business-questions` - список типових бізнес-питань.
- `prompt: sales_report_prompt` - шаблон для AI sales analyst.

## Перевірка FastMCP entrypoint

```bash
fastmcp inspect sales_mcp_server.py:mcp
fastmcp run fastmcp.json
```

`fastmcp.json` описує production-style запуск через HTTP transport. MCP endpoint буде доступний на `/mcp/`.

## Deploy to Prefect Horizon

1. Push this repo to GitHub.
2. Open `https://horizon.prefect.io/` and choose the GitHub repo.
3. Configure the server with:
   - Server name: `sales-analytics` або інше унікальне ім'я.
   - Entrypoint: `sales_mcp_server.py:mcp`.
   - Authentication: увімкніть, якщо сервер має бути доступний тільки для вашої організації.
4. Horizon має автоматично встановити dependencies з `requirements.txt`.
5. Після deploy перевірте tools/resources/prompts у Horizon Inspector.

Очікуваний remote MCP endpoint матиме формат:

```text
https://<server-name>.fastmcp.app/mcp
```

## Запуск як MCP server

```bash
python3 -m pip install -r requirements.txt
python3 sales_mcp_server.py
```

Після цього сервер можна підключати до MCP host, який підтримує локальні `stdio` сервери.

Для HTTP запуску поза Horizon:

```bash
python3 sales_mcp_server.py --http
```

За замовчуванням HTTP server слухає `0.0.0.0:8000`, а health check доступний на `/health`. Якщо platform задає `PORT`, сервер автоматично запуститься в HTTP mode.

Приклад конфігурації для host, який очікує команду запуску:

```json
{
  "mcpServers": {
    "sales-analytics": {
      "command": "python3",
      "args": [
        "/absolute/path/to/sales_mcp_server.py"
      ]
    }
  }
}
```

## Бізнес-сценарій для показу

1. Агент читає `sales://business-questions`.
2. Агент викликає `load_sales_summary`.
3. Агент викликає `top_products` для `revenue` або `gross_profit`.
4. Агент викликає `monthly_sales_report`.
5. Агент використовує `sales_report_prompt` і готує короткий Markdown-звіт.

## Обмеження безпеки

- tools читають тільки CSV-файли всередині цієї демо-папки;
- абсолютні шляхи заборонені;
- файли поза демо-папкою заборонені;
- сервер нічого не записує на диск;
- сервер не використовує мережу й API keys.
