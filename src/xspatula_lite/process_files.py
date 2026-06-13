from __future__ import annotations

from pathlib import Path
from typing import Any

from xspatula_lite.exceptions import ConfigError
from xspatula_lite.utils import read_json
from xspatula_lite.models import ProcessStep


class ProcessFileLoader:
    """Load Process JSON files into executable ProcessStep objects."""

    RESERVED_KEYS = {"process_id", "process", "parameters", "execute", "verbose", "overwrite", "delete"}

    def load(self, path: str | Path) -> list[ProcessStep]:
        p = Path(path).expanduser().resolve()
        raw = read_json(p)
        definitions = raw.get("process")
        if isinstance(definitions, dict):
            definitions = [definitions]
        if not isinstance(definitions, list):
            raise ConfigError(f"Process JSON must contain a process list or object: {p}")

        steps: list[ProcessStep] = []
        for index, definition in enumerate(definitions, start=1):
            if not isinstance(definition, dict):
                raise ConfigError(f"Process definition #{index} must be an object in {p}")
            steps.append(self._to_step(definition, source_file=p, index=index))
        return steps

    def from_process(self, process: str, parameters: dict[str, Any] | None = None) -> ProcessStep:
        return ProcessStep(
            source_file=None,
            index=1,
            process_id=process,
            parameters=parameters or {},
            options={},
            raw={"process": process, "parameters": parameters or {}},
        )

    def _to_step(self, definition: dict[str, Any], *, source_file: Path, index: int) -> ProcessStep:
        process_id = definition.get("process_id") or definition.get("process")
        if not process_id:
            raise ConfigError(f"Missing process_id/process in {source_file} step #{index}")

        parameters = dict(definition.get("parameters") or {})
        # Original files sometimes put schema/table directly at process level.
        for key, value in definition.items():
            if key not in self.RESERVED_KEYS:
                parameters.setdefault(key, value)

        options = {
            key: definition[key]
            for key in ("execute", "verbose", "overwrite", "delete")
            if key in definition
        }
        return ProcessStep(
            source_file=source_file,
            index=index,
            process_id=str(process_id),
            parameters=parameters,
            options=options,
            raw=definition,
        )
