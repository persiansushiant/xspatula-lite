from __future__ import annotations

from collections import defaultdict
from typing import Any

from xspatula_lite.models import ProcessStep


class ProcessRegistry:
    """In-memory metadata registry for root_process/process/parameters/nodes/permissions.

    This mirrors the old idea that the database is also a metadata registry,
    but keeps it mockable and package-local for the first implementation.
    """

    def __init__(self):
        self.root_processes: dict[str, dict[str, Any]] = {}
        self.processes: dict[str, dict[str, Any]] = {}
        self.parameters: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.nodes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.permissions: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def register_from_step(self, step: ProcessStep) -> None:
        p = step.parameters
        process_id = step.process_id
        if process_id in {"root_process", "add_root_process"}:
            self.add_root_process(p)
        elif process_id in {"process", "add_process"}:
            self.add_process(p)
        elif process_id in {"parameters", "parameter", "process_parameter"}:
            self.add_parameters(p)
        elif process_id == "nodes":
            self.add_nodes(p)
        elif process_id == "permissions":
            self.add_permissions(p)
        else:
            # Runtime process call: keep a minimal trace.
            self.processes.setdefault(process_id, {"process": process_id, "parameters": p})

    def add_root_process(self, data: dict[str, Any]) -> None:
        key = data.get("root_process") or data.get("id")
        if not key:
            raise ValueError("root_process registration requires root_process or id")
        self.root_processes[str(key)] = dict(data)
        print(f"[registry] root_process registered: {key}")

    def add_process(self, data: dict[str, Any]) -> None:
        key = data.get("process") or data.get("process_id") or data.get("id")
        if not key:
            raise ValueError("process registration requires process/process_id/id")
        self.processes[str(key)] = dict(data)
        print(f"[registry] process registered: {key}")

    def add_parameters(self, data: dict[str, Any]) -> None:
        process = str(data.get("process") or data.get("process_id") or "unknown")
        items = data.get("parameters") if isinstance(data.get("parameters"), list) else [data]
        self.parameters[process].extend(dict(item) for item in items)
        print(f"[registry] parameters registered for: {process}")

    def add_nodes(self, data: dict[str, Any]) -> None:
        process = str(data.get("process") or data.get("process_id") or "unknown")
        items = data.get("nodes") if isinstance(data.get("nodes"), list) else [data]
        self.nodes[process].extend(dict(item) for item in items)
        print(f"[registry] nodes registered for: {process}")

    def add_permissions(self, data: dict[str, Any]) -> None:
        process = str(data.get("process") or data.get("process_id") or "unknown")
        items = data.get("permissions") if isinstance(data.get("permissions"), list) else [data]
        self.permissions[process].extend(dict(item) for item in items)
        print(f"[registry] permissions registered for: {process}")
