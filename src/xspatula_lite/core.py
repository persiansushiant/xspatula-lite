from __future__ import annotations

from pathlib import Path
from typing import Any

from xspatula_lite.database import DatabaseSession
from xspatula_lite.dispatcher import Dispatcher
from xspatula_lite.exceptions import ConfigError
from xspatula_lite.handlers.setup_handlers import SetupHandlers
from xspatula_lite.jobs import JobLoader
from xspatula_lite.models import Job, Scheme
from xspatula_lite.pilot import PilotLoader
from xspatula_lite.process_files import ProcessFileLoader
from xspatula_lite.registry import ProcessRegistry
from xspatula_lite.scheme import SchemeLoader


class Xspatula:
    """Facade for notebook-free metadata-driven workflow execution."""

    def __init__(self, *, mock: bool = True, verbose: int | None = None):
        self.mock = mock
        self.verbose_override = verbose
        self.scheme: Scheme | None = None
        self.job: Job | None = None
        self.registry = ProcessRegistry()
        self.db = DatabaseSession(mock=mock, verbose=verbose if verbose is not None else 1)
        self.dispatcher = Dispatcher(registry=self.registry, verbose=verbose if verbose is not None else 1)
        self.scheme_loader = SchemeLoader()
        self.job_loader = JobLoader()
        self.pilot_loader = PilotLoader()
        self.process_file_loader = ProcessFileLoader()
        self._install_builtin_handlers()

    def load_scheme(self, path: str | Path) -> Scheme:
        self.scheme = self.scheme_loader.load(path)
        verbose = int(self.scheme.defaults.get("verbose", self.db.verbose))
        if self.verbose_override is not None:
            verbose = self.verbose_override
        self.db.config = self.scheme.database
        self.db.verbose = verbose
        self.dispatcher.verbose = verbose
        self.db.connect()
        return self.scheme

    def run_job(self, job_name: str) -> None:
        scheme = self._require_scheme()
        self.job = self.job_loader.load(scheme, job_name)
        defaults = dict(scheme.defaults)
        defaults.update(self.job.defaults)
        self.run_pilot(
            self.job.pilot_path,
            process_folder=self.job.process_folder_path,
            defaults=defaults,
        )

    def run_pilot(
        self,
        pilot_path: str | Path,
        *,
        process_folder: str | Path | None = None,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        scheme = self._require_scheme()
        pilot = Path(pilot_path).expanduser().resolve()
        base = Path(process_folder).expanduser().resolve() if process_folder else pilot.parent
        effective_defaults = defaults or scheme.defaults
        for process_file in self.pilot_loader.load(pilot):
            self.run_process_file(base / process_file, defaults=effective_defaults)

    def run_process_file(self, path: str | Path, *, defaults: dict[str, Any] | None = None) -> None:
        scheme = self._require_scheme()
        for step in self.process_file_loader.load(path):
            self.dispatcher.dispatch(step, defaults=defaults or scheme.defaults)

    def run_process(self, process: str, parameters: dict[str, Any] | None = None) -> None:
        scheme = self._require_scheme()
        step = self.process_file_loader.from_process(process, parameters)
        self.dispatcher.dispatch(step, defaults=scheme.defaults)

    def register_handler(self, process_id: str, handler) -> None:
        self.dispatcher.register(process_id, handler)

    def close(self) -> None:
        self.db.close()

    def _require_scheme(self) -> Scheme:
        if self.scheme is None:
            raise ConfigError("Call load_scheme(path) before running jobs or processes.")
        return self.scheme

    def _install_builtin_handlers(self) -> None:
        setup = SetupHandlers(self.db)
        self.dispatcher.register_many({
            "create_schema": setup.create_schema,
            "create_table": setup.create_table,
            "table_insert": setup.table_insert,
            "table_update": setup.table_update,
            "delete_table": setup.delete_table,
            "delete_schema": setup.delete_schema,
            "delete_database": setup.delete_database,
        })
