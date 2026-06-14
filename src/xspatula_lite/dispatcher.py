from __future__ import annotations

from collections.abc import Callable
from typing import Any

from xspatula_lite.exceptions import DispatchError
from xspatula_lite.models import ProcessStep
from xspatula_lite.registry import ProcessRegistry

Handler = Callable[[ProcessStep], None]


class Dispatcher:
    """Map process_id/process names to Python handlers."""

    def __init__(
        self,
        *,
        registry: ProcessRegistry | None = None,
        verbose: int = 1,
    ):
        self.handlers: dict[str, Handler] = {}
        self.registry = registry or ProcessRegistry()
        self.verbose = verbose

        self.register_registry_handlers()

    def register(self, process_id: str, handler: Handler) -> None:
        self.handlers[process_id] = handler

    def register_many(self, mapping: dict[str, Handler]) -> None:
        for process_id, handler in mapping.items():
            self.register(process_id, handler)

    def register_registry_handlers(self) -> None:
        registry_process_ids = set(self.registry.ENTITY_PROCESS_IDS)
        registry_process_ids.update(self.registry.PROCESS_ID_ALIASES.keys())

        for process_id in registry_process_ids:
            self.register(
                process_id,
                self.registry.register_from_step,
            )

    def dispatch(
        self,
        step: ProcessStep,
        *,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        merged_options = dict(defaults or {})
        merged_options.update(step.options)

        effective = ProcessStep(
            source_file=step.source_file,
            index=step.index,
            process_id=step.process_id,
            parameters=step.parameters,
            options=merged_options,
            raw=step.raw,
        )

        if not effective.options.get("execute", True):
            self._log(f"[skip] {effective.label}")
            return

        handler = self.handlers.get(effective.process_id)

        if handler is None:
            if effective.process_id in {"nodes", "permissions"}:
                handler = self.registry.register_from_step
            else:
                raise DispatchError(
                    f"No handler registered for process_id "
                    f"'{effective.process_id}'"
                )

        self._log(f"[dispatch] {effective.label}")

        handler(effective)

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)