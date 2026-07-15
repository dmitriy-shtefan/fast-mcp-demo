from fastmcp import FastMCP

mcp = FastMCP("WeatherServer")

@mcp.tool
def get_weather(city: str) -> str:
    return f"Сонячно, +24°C у {city}"

if __name__ == "__main__":
    mcp.run()
