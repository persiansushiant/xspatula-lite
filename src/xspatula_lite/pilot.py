from __future__ import annotations

from pathlib import Path

from xspatula_lite.utils import read_pilot_lines


class PilotLoader:
    """Read pilot txt files and return ordered process JSON filenames."""

    def load(self, path: str | Path) -> list[str]:
        return read_pilot_lines(path)
