from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xspatula_lite.exceptions import ConfigError
from xspatula_lite.scheme import Scheme
from xspatula_lite.utils import read_json


@dataclass
class Job:
    job_id: str
    pilot_path: Path
    process_folder_path: Path
    defaults: dict[str, Any]
    raw: dict[str, Any]
    layout: str


class JobLoader:
    def load(self, scheme: Scheme, job_name: str) -> Job:
        job_path = self.resolve_job_path(scheme, job_name)
        raw = read_json(job_path)

        if self._is_clean_job(raw):
            return self._load_clean_job(
                scheme=scheme,
                job_name=job_name,
                raw=raw,
            )

        if self._is_legacy_job(raw):
            return self._load_legacy_job(
                scheme=scheme,
                job_name=job_name,
                raw=raw,
            )

        raise ConfigError(
            f"Invalid job contract in {job_path}. "
            "Expected clean job contract with keys "
            "'job_id', 'pilot', 'process_folder' "
            "or legacy contract with 'process.job_folder', "
            "'process.process_sub_folder', 'process.pilot_file'."
        )

    def resolve_job_path(self, scheme: Scheme, job_name: str) -> Path:
        candidates = [
            Path(scheme.jobs_path) / f"{job_name}.json",
            Path(scheme.jobs_path) / f"job_{job_name}.json",
            Path(scheme.project_path) / f"job_{job_name}.json",
            Path(scheme.project_path) / f"{job_name}.json",
            Path(job_name),
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        searched = "\n".join(str(c) for c in candidates)

        raise ConfigError(
            f"Could not find job '{job_name}'. Searched:\n{searched}"
        )

    def _is_clean_job(self, raw: dict[str, Any]) -> bool:
        return (
            "job_id" in raw
            and "pilot" in raw
            and "process_folder" in raw
        )

    def _is_legacy_job(self, raw: dict[str, Any]) -> bool:
        process = raw.get("process")

        if not isinstance(process, dict):
            return False

        return (
            "job_folder" in process
            and "process_sub_folder" in process
            and "pilot_file" in process
        )

    def _load_clean_job(
        self,
        scheme: Scheme,
        job_name: str,
        raw: dict[str, Any],
    ) -> Job:
        job_id = raw.get("job_id", job_name)

        pilot_path = (
            Path(scheme.pilots_path)
            / raw["pilot"]
        ).resolve()

        process_folder_path = (
            Path(scheme.processes_path)
            / raw["process_folder"]
        ).resolve()

        if not pilot_path.exists():
            raise ConfigError(f"Pilot file not found: {pilot_path}")

        if not process_folder_path.exists():
            raise ConfigError(
                f"Process folder not found: {process_folder_path}"
            )

        return Job(
            job_id=job_id,
            pilot_path=pilot_path,
            process_folder_path=process_folder_path,
            defaults=raw.get("defaults", {}),
            raw=raw,
            layout="clean",
        )

    def _load_legacy_job(
        self,
        scheme: Scheme,
        job_name: str,
        raw: dict[str, Any],
    ) -> Job:
        process = raw["process"]

        job_folder = process["job_folder"]
        process_sub_folder = process["process_sub_folder"]
        pilot_file = process["pilot_file"]

        job_root = (
            Path(scheme.jobs_path)
            / job_folder
        ).resolve()

        pilot_path = (
            job_root
            / pilot_file
        ).resolve()

        process_folder_path = (
            job_root
            / process_sub_folder
        ).resolve()

        if not pilot_path.exists():
            raise ConfigError(f"Pilot file not found: {pilot_path}")

        if not process_folder_path.exists():
            raise ConfigError(
                f"Process folder not found: {process_folder_path}"
            )

        return Job(
            job_id=job_name,
            pilot_path=pilot_path,
            process_folder_path=process_folder_path,
            defaults=raw.get("defaults", {}),
            raw=raw,
            layout="legacy",
        )