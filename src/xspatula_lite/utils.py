from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from xspatula_lite.exceptions import ConfigError


def as_path(path: str | Path) -> Path:
    """Return an expanded Path without forcing it to exist."""
    return Path(path).expanduser()


def resolve_path(path: str | Path, *, base: str | Path | None = None) -> Path:
    """Resolve a possibly relative path against a base folder."""
    p = as_path(path)
    if not p.is_absolute() and base is not None:
        p = as_path(base) / p
    return p.resolve()


def read_json(path: str | Path) -> dict[str, Any]:
    """Read a JSON file whose root must be an object."""
    p = resolve_path(path)
    if not p.is_file():
        raise ConfigError(f"JSON file not found: {p}")
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {p}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"JSON root must be an object: {p}")
    return data


def write_json(path: str | Path, data: dict[str, Any], *, indent: int = 2) -> None:
    """Write a JSON object, creating parent folders as needed."""
    p = resolve_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.write("\n")


def read_pilot_lines(path: str | Path) -> list[str]:
    """Read pilot lines, ignoring empty lines and comments starting with #."""
    p = resolve_path(path)
    if not p.is_file():
        raise ConfigError(f"Pilot file not found: {p}")
    lines: list[str] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            lines.append(cleaned)
    return lines


def require_keys(data: dict[str, Any], keys: list[str], *, context: str) -> None:
    """Raise a clean ConfigError if required keys are missing."""
    missing = [key for key in keys if key not in data]
    if missing:
        pretty = ", ".join(missing)
        raise ConfigError(f"Missing required key(s) in {context}: {pretty}")
