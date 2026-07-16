import sys
from importlib.metadata import distribution


def main() -> None:
    entry_point = next(
        entry_point
        for entry_point in distribution("fastmcp").entry_points
        if entry_point.group == "console_scripts"
        and entry_point.name == "fastmcp"
    )

    sys.argv[0] = "fastmcp"
    entry_point.load()()


if __name__ == "__main__":
    main()