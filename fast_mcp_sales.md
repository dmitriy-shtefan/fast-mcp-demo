# Технічне завдання

## 1. Мета

Створити мінімальний MCP-сервер на Python для аналізу локального CSV-файлу з продажами. 
Сервер має показати різницю між трьома складовими MCP:

```text
Resource -> Tool -> Prompt -> Markdown-звіт
```

У сервері має бути один tool, один resource і один prompt.

## 2. Основний сценарій користувача

1. AI-агент підключається до MCP-сервера.
2. Читає resource `sales://metric-definitions`, щоб зрозуміти значення метрик.
3. Викликає tool `load_sales_summary` для файлу `sales_data.csv`.
4. Використовує prompt `sales_report_prompt` для підготовки короткого звіту українською мовою.
5. Агент формує відповідь лише на основі даних tool і resource.

## 3. Технічні вимоги

| Компонент | Вимога |
|---|---|
| Мова | Python 3 |
| MCP framework | `fastmcp` |
| Основний файл | `sales_mcp_server.py` |
| Дані | Локальний файл `sales_data.csv` |
| Режим за замовчуванням | MCP через `stdio` |
| HTTP transport | `stateless_http=True` |
| HTTP host | `0.0.0.0` за замовчуванням |
| HTTP port | `8000` за замовчуванням |
| Health check | `GET /health` |
| Доступ до даних | Лише читання CSV у директорії проєкту |

## 4. Дані та розрахунки

Файл `sales_data.csv` містить такі колонки:

| Поле | Тип | Опис |
|---|---|---|
| `order_id` | string | Ідентифікатор замовлення |
| `date` | `YYYY-MM-DD` | Дата замовлення |
| `region` | string | Регіон продажу |
| `channel` | string | Канал продажу |
| `product` | string | Продукт |
| `category` | string | Категорія продукту |
| `quantity` | integer | Кількість проданих одиниць |
| `unit_price` | float | Ціна за одиницю, UAH |
| `cost_per_unit` | float | Собівартість одиниці, UAH |
| `customer_segment` | string | Сегмент клієнта |

Для кожного рядка обчислюйте:

```text
revenue = quantity × unit_price
gross_profit = quantity × (unit_price - cost_per_unit)
```

Для розрахунку tool обов’язково потребує лише колонки `quantity`, `unit_price` та `cost_per_unit`; решта колонок залишаються в CSV як бізнес-контекст.

Грошові значення та відсотки потрібно округлювати до двох знаків після коми. Якщо виручка дорівнює нулю, валова маржа має дорівнювати `0`.

## 5. MCP Components

| Тип | Назва / URI | Призначення |
|---|---|---|
| Tool | `load_sales_summary` | Читає CSV і розраховує зведення продажів |
| Resource | `sales://metric-definitions` | Повертає статичні визначення метрик |
| Prompt | `sales_report_prompt` | Повертає інструкцію для AI sales analyst |

### 5.1. Tool: `load_sales_summary`

Реалізуйте tool із сигнатурою:

```python
def load_sales_summary(file_name: str = "sales_data.csv") -> dict[str, Any]:
```

Tool повертає словник із полями:

| Поле | Опис |
|---|---|
| `file` | Назва проаналізованого файлу |
| `orders` | Кількість замовлень |
| `revenue_uah` | Загальна виручка |
| `gross_profit_uah` | Загальний валовий прибуток |
| `gross_margin_pct` | Валова маржа у відсотках |

Для порожнього CSV tool має повертати:

```python
{"file": file_name, "orders": 0, "message": "CSV file is empty"}
```

### 5.2. Resource: `sales://metric-definitions`

Resource не виконує обчислень. Він має повернути **саме цей текст**:

```text
Визначення метрик продажів:

- revenue_uah — виручка в гривнях: quantity × unit_price.
- gross_profit_uah — валовий прибуток у гривнях: quantity × (unit_price - cost_per_unit).
- gross_margin_pct — валова маржа у відсотках: gross_profit / revenue × 100.
- orders — кількість рядків із замовленнями у CSV.
```

### 5.3. Prompt: `sales_report_prompt`

Реалізуйте prompt із сигнатурою:

```python
def sales_report_prompt(company_context: str = "B2B SaaS компанія") -> str:
```

Prompt має повернути **саме цей текст**, підставивши значення параметра замість `{company_context}`:

```text
Ви - AI sales analyst для компанії: {company_context}.

Підготуйте короткий Markdown-звіт українською мовою:
1. Стислий executive summary на 2-3 речення.
2. Основні метрики: orders, revenue, gross profit, margin.
3. 2-3 практичні бізнес-рекомендації.

Використовуйте тільки факти, отримані з MCP tools або resources.
Не вигадуйте замовлення, продукти, суми або тренди.
```

## 6. Безпека та запуск

### Безпека файлів

| Сценарій | Очікувана поведінка |
|---|---|
| Абсолютний шлях у `file_name` | `ValueError` |
| Шлях поза директорією проєкту | `ValueError` |
| Файл не має розширення `.csv` | `ValueError` |
| Файл не існує | `FileNotFoundError` |
| У CSV немає обов’язкових колонок | `ValueError` з переліком колонок |
| Будь-який запис у файл | Заборонено |

### Запуск через stdio

```bash
python3 sales_mcp_server.py
```

### Запуск через HTTP

```bash
python3 sales_mcp_server.py --http
```

HTTP-режим також має вмикатися, якщо `MCP_TRANSPORT` має значення `http` або `streamable-http`, або задано змінну середовища `PORT`.

Endpoint `GET /health` має повертати:

```json
{"status": "ok", "service": "sales-analytics-mcp"}
```

## 7. Перевірочні prompt-и

1. Покажи загальне зведення продажів за доступним CSV.
2. Які revenue, gross profit і gross margin за весь період?
3. Скільки замовлень містить файл і якою є загальна виручка?
4. Яка валова маржа за весь період?
5. Прочитай resource `sales://metric-definitions`, а потім поясни результати `load_sales_summary` простими словами.
6. Використай `sales_report_prompt` і підготуй короткий Markdown-звіт українською.
7. Спробуй проаналізувати файл `../sales_data.csv` і поясни, чому це заборонено.
8. Спробуй проаналізувати файл `requirements.txt` і поясни, чому це заборонено.

## 8. Acceptance Criteria

| Критерій | Очікувана поведінка |
|---|---|
| MCP components | `fastmcp inspect sales_mcp_server.py:mcp` показує рівно 1 tool, 1 resource і 1 prompt |
| Tool | `load_sales_summary` коректно розраховує всі метрики для `sales_data.csv` |
| Resource | Доступний за URI `sales://metric-definitions` і повертає повний текст із розділу 5.2 |
| Prompt | Приймає `company_context` і повертає повний текст із розділу 5.3 |
| Помилки файлів | Некоректні шляхи, не-CSV, відсутній файл і неправильна схема обробляються за розділом 6 |
| Health check | `GET /health` повертає HTTP 200 і визначений JSON |
| Read-only | Сервер не змінює та не створює файли даних |
