from __future__ import annotations

from pathlib import Path
from typing import Any

from xspatula_lite.models import Scheme
from xspatula_lite.utils import read_json, resolve_path


class SchemeLoader:
    """Load the top-level execution scheme.

    Preferred project layout:

        project/
          schemes/local.json
          jobs/*.json
          pilots/*.txt
          processes/<job>/*.json

    Legacy Xspatula-style scheme files are still tolerated.
    """

    DEFAULT_PATHS = {
        "jobs": "jobs",
        "pilots": "pilots",
        "processes": "processes",
    }

    def load(self, path: str | Path) -> Scheme:
        scheme_path = Path(path).expanduser().resolve()
        raw = read_json(scheme_path)

        project_path_raw = raw.get("project_path", ".")
        project_path = resolve_path(project_path_raw, base=scheme_path.parent)

        paths = self._resolve_project_paths(raw, project_path)
        defaults = self._extract_defaults(raw)
        database = raw.get("database") or raw.get("postgresdb") or {}
        user_project = raw.get("user_project") or {}

        return Scheme(
            raw=raw,
            path=scheme_path,
            project_path=project_path,
            paths=paths,
            database=database,
            user_project=user_project,
            defaults=defaults,
        )

    def _resolve_project_paths(self, raw: dict[str, Any], project_path: Path) -> dict[str, Path]:
        configured = raw.get("paths") or {}
        paths: dict[str, Path] = {}
        for key, default_value in self.DEFAULT_PATHS.items():
            value = configured.get(key, default_value)
            paths[key] = resolve_path(value, base=project_path)
        return paths

    @staticmethod
    def _extract_defaults(raw: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "execute": True,
            "verbose": 1,
            "overwrite": False,
            "delete": False,
        }

        # New cleaner style.
        if isinstance(raw.get("defaults"), dict):
            defaults.update(raw["defaults"])

        # Legacy style from the previous Xspatula files.
        process_defaults = raw.get("process")
        if isinstance(process_defaults, list) and process_defaults and isinstance(process_defaults[0], dict):
            defaults.update(process_defaults[0])
        elif isinstance(process_defaults, dict):
            # Only use scalar default-like values, not nested job configs.
            for key in ("execute", "verbose", "overwrite", "delete"):
                if key in process_defaults:
                    defaults[key] = process_defaults[key]

        return defaults
