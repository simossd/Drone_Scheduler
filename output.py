from typing import Any

RESET = "\033[0m"

PALETTE = [
    "\033[38;5;196m",
    "\033[38;5;46m",
    "\033[38;5;226m",
    "\033[38;5;33m",
    "\033[38;5;201m",
    "\033[38;5;51m",
    "\033[38;5;208m",
    "\033[38;5;154m",
    "\033[38;5;220m",
    "\033[38;5;39m",
    "\033[38;5;177m",
    "\033[38;5;51m",
]

COLOR_MAP = {
    "red": "\033[38;5;196m",
    "green": "\033[38;5;46m",
    "yellow": "\033[38;5;226m",
    "blue": "\033[38;5;21m",
    "magenta": "\033[38;5;201m",
    "cyan": "\033[38;5;51m",
    "white": "\033[38;5;231m",
    "gray": "\033[38;5;244m",
    "grey": "\033[38;5;244m",
    "orange": "\033[38;5;208m",
    "pink": "\033[38;5;218m",
    "purple": "\033[38;5;93m",
    "brown": "\033[38;5;94m",
    "gold": "\033[38;5;220m",
    "lime": "\033[38;5;154m",
    "maroon": "\033[38;5;88m",
    "crimson": "\033[38;5;161m",
    "violet": "\033[38;5;177m",
    "black": "\033[38;5;250m",
    "rainbow": "\033[38;5;213m",
    "darkred": "\033[38;5;124m",
}


def color_code(name: str) -> str:
    """Return a visible ANSI color for any single-word color name."""
    if not name:
        return RESET
    code = COLOR_MAP.get(name.lower())
    if code is not None:
        return code

    total = 0
    for char in name.lower():
        total += ord(char)
    return PALETTE[total % len(PALETTE)]


class Output:
    """Render the simulation output to the terminal."""

    def __init__(self, path: dict[Any, list[tuple]], pf: Any = None) -> None:
        """Store the turn data and render it immediately.

        Args:
            path: Turn-indexed movement data.
            pf: Optional option to track ur move for an easy debug.
        """
        self.path: dict[Any, list[tuple]] = path
        self.pf = pf
        self.zone_attributes: Any = None
        self.n_connection: Any = None
        self.draw()

    def draw(self) -> None:
        """Print the colored simulation turns."""
        if self.path:
            for _, turn_n in self.path.items():
                for drone, hub, color in turn_n:
                    c = color_code(color)
                    print(f'{c}{drone}-{hub} {RESET}', end=' ')
                print()
        print('\nTurnes:', len(self.path.keys()))
