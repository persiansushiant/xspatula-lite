from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xspatula_lite.utils import read_json


@dataclass
class Scheme:
    raw: dict[str, Any]
    scheme_path: Path
    project_path: Path
    jobs_path: Path
    pilots_path: Path
    processes_path: Path
    database: dict[str, Any]
    user_project: dict[str, Any]
    defaults: dict[str, Any]


class SchemeLoader:
    def load(self, path: str | Path) -> Scheme:
        scheme_path = Path(path).resolve()
        raw = read_json(scheme_path)

        scheme_dir = scheme_path.parent

        project_path = (
            scheme_dir
            / raw.get("project_path", ".")
        ).resolve()

        paths = raw.get("paths", {})

        jobs_path = (
            project_path
            / paths.get("jobs", "jobs")
        ).resolve()

        pilots_path = (
            project_path
            / paths.get("pilots", "pilots")
        ).resolve()

        processes_path = (
            project_path
            / paths.get("processes", "processes")
        ).resolve()

        database = (
            raw.get("database")
            or raw.get("postgresdb")
            or {"type": "mock"}
        )

        defaults = self._extract_defaults(raw)

        return Scheme(
            raw=raw,
            scheme_path=scheme_path,
            project_path=project_path,
            jobs_path=jobs_path,
            pilots_path=pilots_path,
            processes_path=processes_path,
            database=database,
            user_project=raw.get("user_project", {}),
            defaults=defaults,
        )

    def _extract_defaults(self, raw: dict[str, Any]) -> dict[str, Any]:
        defaults = {
            "execute": True,
            "verbose": 0,
            "overwrite": False,
            "delete": False,
        }

        if isinstance(raw.get("defaults"), dict):
            defaults.update(raw["defaults"])

        process_defaults = raw.get("process")

        if isinstance(process_defaults, list) and process_defaults:
            first = process_defaults[0]

            if isinstance(first, dict):
                for key in [
                    "execute",
                    "verbose",
                    "overwrite",
                    "delete",
                    "src_path",
                ]:
                    if key in first:
                        defaults[key] = first[key]

        elif isinstance(process_defaults, dict):
            for key in [
                "execute",
                "verbose",
                "overwrite",
                "delete",
                "src_path",
            ]:
                if key in process_defaults:
                    defaults[key] = process_defaults[key]

        return defaults