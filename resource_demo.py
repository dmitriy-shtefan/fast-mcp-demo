from fastmcp import FastMCP


mcp = FastMCP("CourseInfoServer")


@mcp.resource("course://info")
def get_course_info() -> str:
    return """\
Курс: Створення AI-додатків з Python
Тема заняття: MCP і FastMCP

Resource містить дані, які клієнт може прочитати за URI.
На відміну від tool, він не виконує дію і не приймає параметри.
"""


if __name__ == "__main__":
    mcp.run()
