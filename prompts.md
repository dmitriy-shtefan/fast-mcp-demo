Покажи загальну sales summary по доступному CSV.

Який загальний revenue, gross profit, gross margin і average order value за весь період?

Покажи топ 5 продуктів за revenue.

Покажи топ продуктів за gross_profit і поясни, чому вони найприбутковіші.

Який продукт продався у найбільшій кількості одиниць?

Покажи monthly sales report і коротко поясни динаміку по місяцях.

Який місяць мав найбільший revenue?

Порівняй revenue by region і назви 2 найсильніші регіони.

Порівняй revenue by channel: Online, Direct, Partner.

Прочитай resource sales://business-questions і дай відповіді на всі питання, використовуючи tools.

Прочитай sample CSV resource і коротко опиши, які поля є в датасеті.

Використай sales_report_prompt і підготуй короткий Markdown-звіт українською.

Підготуй executive summary для CEO: що відбувається з продажами і які 3 дії варто зробити?

Знайди найсильніший канал продажів і поясни це цифрами.

Чи зростають продажі від квітня до червня 2026? Підтверди цифрами з monthly report.




Для edge-case перевірки tools:


Виклич top_products з limit=3 і metric=quantity.

Виклич top_products з metric=gross_profit.

Спробуй викликати top_products з limit=25 і поясни помилку.

Спробуй проаналізувати файл ../sales_data.csv і поясни, чому це заборонено.

Спробуй проаналізувати файл README.md і поясни, чому це заборонено.