from __future__ import annotations

from pathlib import Path
from typing import Any

from xspatula_lite.database import DatabaseSession
from xspatula_lite.dispatcher import Dispatcher
from xspatula_lite.jobs import JobLoader
from xspatula_lite.operations.db_setup import SetupHandlers
from xspatula_lite.pilot import PilotLoader
from xspatula_lite.process_files import ProcessFileLoader
from xspatula_lite.process_registry import ProcessRegistry
from xspatula_lite.scheme import Scheme, SchemeLoader


class Xspatula:
    def __init__(
        self,
        *,
        mock: bool | None = None,
        verbose: int | bool = 1,
    ):
        self.mock = mock
        self.verbose = verbose

        self.scheme: Scheme | None = None
        self.job = None

        self.scheme_loader = SchemeLoader()
        self.job_loader = JobLoader()
        self.pilot_loader = PilotLoader()
        self.process_file_loader = ProcessFileLoader()

        self.db: DatabaseSession | None = None

        self.registry: ProcessRegistry = ProcessRegistry(
            db=None,
            verbose=self.verbose,
        )

        self.dispatcher: Dispatcher = Dispatcher(
            registry=self.registry,
            verbose=self.verbose,
        )

    def load_scheme(self, scheme_path: str | Path) -> None:
        self.scheme = self.scheme_loader.load(scheme_path)

        self.db = DatabaseSession(
            config=self.scheme.database,
            mock=self.mock,
            verbose=self.verbose,
        )

        if self.scheme.database.get("auto_create", False):
            self.db.create_database_if_missing()

        self.db.connect()

        self.registry = ProcessRegistry(
            db=self.db,
            verbose=self.verbose,
        )

        self.dispatcher = Dispatcher(
            registry=self.registry,
            verbose=self.verbose,
        )

        setup_handlers = SetupHandlers(self.db)

        self.dispatcher.register_many(
            {
                "create_schema": setup_handlers.create_schema,
                "create_table": setup_handlers.create_table,
                "table_insert": setup_handlers.table_insert,
                "table_update": setup_handlers.table_update,
                "grant": setup_handlers.grant,
                "delete_table": setup_handlers.delete_table,
                "delete_schema": setup_handlers.delete_schema,
                "delete_database": setup_handlers.delete_database,
            }
        )

    def run_job(self, job_name: str) -> None:
        scheme = self._require_scheme()
        dispatcher = self._require_dispatcher()

        self.job = self.job_loader.load(
            scheme,
            job_name,
        )

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

        pilot = Path(pilot_path)

        if process_folder is None:
            base = pilot.parent
        else:
            base = Path(process_folder)

        effective_defaults = defaults or scheme.defaults

        for process_file in self.pilot_loader.load(pilot):
            self.run_process_file(
                base / process_file,
                defaults=effective_defaults,
            )

    def run_process_file(
        self,
        path: str | Path,
        *,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        scheme = self._require_scheme()
        dispatcher = self._require_dispatcher()

        for step in self.process_file_loader.load(path):
            dispatcher.dispatch(
                step,
                defaults=defaults or scheme.defaults,
            )

    def run_process(
        self,
        process_id: str,
        parameters: dict[str, Any] | None = None,
        *,
        options: dict[str, Any] | None = None,
    ) -> None:
        scheme = self._require_scheme()
        dispatcher = self._require_dispatcher()

        step = self.process_file_loader.from_process(
            process_id,
            parameters or {},
            options=options or {},
        )

        dispatcher.dispatch(
            step,
            defaults=scheme.defaults,
        )

    def close(self) -> None:
        if self.db is not None:
            self.db.close()

    def _require_scheme(self) -> Scheme:
        if self.scheme is None:
            raise RuntimeError(
                "Scheme is not loaded. Call load_scheme() first."
            )

        return self.scheme

    def _require_dispatcher(self) -> Dispatcher:
        if self.dispatcher is None:
            raise RuntimeError(
                "Dispatcher is not initialized. Call load_scheme() first."
            )

        return self.dispatcher