from __future__ import annotations

from pathlib import Path

from xspatula_lite.exceptions import ConfigError
from xspatula_lite.models import Job, Scheme
from xspatula_lite.utils import read_json, resolve_path, require_keys


class JobLoader:
    """Load job metadata.

    Preferred location: <project>/jobs/<job_name>.json
    Legacy location:    <project>/job_<job_name>.json
    """

    def load(self, scheme: Scheme, job_name: str) -> Job:
        job_path = self.resolve_job_path(scheme, job_name)
        raw = read_json(job_path)

        # Preferred clean format.
        if "pilot" in raw or "process_folder" in raw:
            return self._load_clean_job(scheme, job_name, job_path, raw)

        # Legacy format: {"process": {"job_folder": ..., ...}}
        job_config = raw.get("process", raw)
        if isinstance(job_config, dict) and {"job_folder", "process_sub_folder", "pilot_file"}.issubset(job_config):
            return self._load_legacy_job(job_name, job_path, raw, job_config)

        raise ConfigError(
            f"Invalid job file: {job_path}. Expected keys 'pilot' and 'process_folder' "
            "or legacy keys 'job_folder', 'process_sub_folder', 'pilot_file'."
        )

    def _load_clean_job(self, scheme: Scheme, job_name: str, job_path: Path, raw: dict) -> Job:
        require_keys(raw, ["pilot", "process_folder"], context=str(job_path))
        job_id = str(raw.get("job_id") or job_name)
        pilot_path = resolve_path(raw["pilot"], base=scheme.paths["pilots"])
        process_folder_path = resolve_path(raw["process_folder"], base=scheme.paths["processes"])
        return Job(
            raw=raw,
            path=job_path,
            job_id=job_id,
            pilot_path=pilot_path,
            process_folder_path=process_folder_path,
            description=str(raw.get("description", "")),
            defaults=dict(raw.get("defaults") or {}),
        )

    def _load_legacy_job(self, job_name: str, job_path: Path, raw: dict, job_config: dict) -> Job:
        job_folder = job_config["job_folder"]
        process_sub_folder = job_config["process_sub_folder"]
        pilot_file = job_config["pilot_file"]
        folder_path = resolve_path(job_folder, base=job_path.parent)
        return Job(
            raw=raw,
            path=job_path,
            job_id=job_name,
            pilot_path=resolve_path(pilot_file, base=folder_path),
            process_folder_path=resolve_path(process_sub_folder, base=folder_path),
            defaults=dict(job_config.get("defaults") or {}),
        )

    @staticmethod
    def resolve_job_path(scheme: Scheme, job_name: str) -> Path:
        name = job_name[:-5] if job_name.endswith(".json") else job_name
        explicit = Path(job_name).expanduser()
        candidates = [
            scheme.paths["jobs"] / f"{name}.json",
            scheme.paths["jobs"] / f"job_{name}.json",
            scheme.project_path / f"job_{name}.json",
            scheme.project_path / f"{name}.json",
            explicit,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        searched = "\n".join(str(c) for c in candidates)
        raise ConfigError(f"Could not find job '{job_name}'. Searched:\n{searched}")
