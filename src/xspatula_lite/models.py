from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Scheme:
    raw: dict[str, Any]
    path: Path
    project_path: Path
    paths: dict[str, Path]
    database: dict[str, Any] = field(default_factory=dict)
    user_project: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Job:
    raw: dict[str, Any]
    path: Path
    job_id: str
    pilot_path: Path
    process_folder_path: Path
    description: str = ""
    defaults: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProcessStep:
    source_file: Path | None
    index: int
    process_id: str
    parameters: dict[str, Any]
    options: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def label(self) -> str:
        source = self.source_file.name if self.source_file else "runtime"
        return f"{source}#{self.index}:{self.process_id}"
