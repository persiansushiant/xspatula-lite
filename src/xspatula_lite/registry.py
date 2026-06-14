from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from xspatula_lite.models import ProcessStep


class ProcessRegistry:
    """In-memory implementation of the confirmed legacy Xspatula metadata registry.

    The legacy project stores metadata in concrete database tables.  This class
    mirrors those framework-level tables in memory so the package can run in
    mock mode before a real PostgreSQL backend is attached.
    """

    ENTITY_PROCESS_IDS = {
        "root_process",
        "add_root_process",
        "process",
        "add_process",
        "process_parameter",
        "parameter",
        "parameters",
        "process_parameter_set_value",
        "process_parameter_minmax",
        "process_parameter_schema_table",
        "process_parameter_permission",
        "process_parameter_default",
    }

    def __init__(self):
        self.root_processes: dict[str, dict[str, Any]] = {}
        self.processes: dict[str, dict[str, Any]] = {}
        self.process_parameters: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.process_parameter_set_values: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.process_parameter_minmax: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.process_parameter_schema_tables: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.process_parameter_permissions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.process_parameter_defaults: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Kept for compatibility with earlier xspatula-lite prototypes.
        self.nodes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.permissions: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def register_from_step(self, step: ProcessStep) -> None:
        data = deepcopy(step.parameters)
        process_id = step.process_id

        if process_id in {"root_process", "add_root_process"}:
            self.add_root_process(data)
        elif process_id in {"process", "add_process"}:
            self.add_process(data)
        elif process_id in {"process_parameter", "parameter", "parameters"}:
            self.add_process_parameter(data)
        elif process_id == "process_parameter_set_value":
            self.add_process_parameter_set_value(data)
        elif process_id == "process_parameter_minmax":
            self.add_process_parameter_minmax(data)
        elif process_id == "process_parameter_schema_table":
            self.add_process_parameter_schema_table(data)
        elif process_id == "process_parameter_permission":
            self.add_process_parameter_permission(data)
        elif process_id == "process_parameter_default":
            self.add_process_parameter_default(data)
        else:
            self.processes.setdefault(process_id, {"process": process_id, "parameters": data})

    def add_root_process(self, data: dict[str, Any]) -> None:
        key = data.get("root_process") or data.get("id")
        if not key:
            raise ValueError("root_process registration requires root_process or id")
        record = dict(data)
        record.setdefault("root_process", key)
        self.root_processes[str(key)] = record
        print(f"[registry] root_process registered: {key}")

    def add_process(self, data: dict[str, Any]) -> None:
        key = data.get("process") or data.get("process_id") or data.get("id")
        if not key:
            raise ValueError("process registration requires process/process_id/id")
        record = dict(data)
        record.setdefault("process", key)
        self.processes[str(key)] = record
        print(f"[registry] process registered: {key}")

    def add_process_parameter(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.process_parameters, data, default_key="process_parameter")

    def add_process_parameter_set_value(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.process_parameter_set_values, data, default_key="process_parameter_set_value")

    def add_process_parameter_minmax(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.process_parameter_minmax, data, default_key="process_parameter_minmax")

    def add_process_parameter_schema_table(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.process_parameter_schema_tables, data, default_key="process_parameter_schema_table")

    def add_process_parameter_permission(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.process_parameter_permissions, data, default_key="process_parameter_permission")

    def add_process_parameter_default(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.process_parameter_defaults, data, default_key="process_parameter_default")

    def add_nodes(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.nodes, data, default_key="nodes")

    def add_permissions(self, data: dict[str, Any]) -> None:
        self._extend_entity(self.permissions, data, default_key="permissions")

    def _extend_entity(
        self,
        store: dict[str, list[dict[str, Any]]],
        data: dict[str, Any],
        *,
        default_key: str,
    ) -> None:
        process_key = self._process_key(data)
        items = self._extract_items(data, default_key=default_key)
        store[process_key].extend(dict(item) for item in items)
        print(f"[registry] {default_key} registered for: {process_key}")

    @staticmethod
    def _process_key(data: dict[str, Any]) -> str:
        return str(data.get("process") or data.get("process_id") or data.get("id") or "unknown")

    @staticmethod
    def _extract_items(data: dict[str, Any], *, default_key: str) -> list[dict[str, Any]]:
        for key in (default_key, "items", "records", "parameters", "values", "permissions"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return [data]

    def snapshot(self) -> dict[str, Any]:
        """Return a serializable registry snapshot for debugging, Flask, tests, or docs."""
        return {
            "root_process": deepcopy(self.root_processes),
            "process": deepcopy(self.processes),
            "process_parameter": deepcopy(dict(self.process_parameters)),
            "process_parameter_set_value": deepcopy(dict(self.process_parameter_set_values)),
            "process_parameter_minmax": deepcopy(dict(self.process_parameter_minmax)),
            "process_parameter_schema_table": deepcopy(dict(self.process_parameter_schema_tables)),
            "process_parameter_permission": deepcopy(dict(self.process_parameter_permissions)),
            "process_parameter_default": deepcopy(dict(self.process_parameter_defaults)),
        }
