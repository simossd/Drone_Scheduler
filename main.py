import sys
from parsing import Parsing
from graph import Graph
from algoo import PathFinder
from output import Output


def main() -> None:
    """Run the drone simulation from a map file."""
    if len(sys.argv) != 2:
        print("ERROR: usage: py main.py <map_file>")
        sys.exit(1)

    parsed = Parsing(sys.argv[1])
    graph = Graph(parsed)

    try:
        pathfinder = PathFinder(graph)
        result = pathfinder.build_output()
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    if not result:
        print("No moves to display.")
        sys.exit(0)

    Output(result, pathfinder)


if __name__ == '__main__':
    main()
