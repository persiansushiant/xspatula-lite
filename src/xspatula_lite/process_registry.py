from __future__ import annotations

from typing import Any


class ProcessRegistry:
    ENTITY_PROCESS_IDS = {
        "root_process",
        "process",
        "process_parameter",
        "process_parameter_set_value",
        "process_parameter_minmax",
        "process_parameter_schema_table",
        "process_parameter_permission",
        "process_parameter_default",
    }

    PROCESS_ID_ALIASES = {
        "add_root_process": "root_process",
        "add_process": "process",
    }

    def __init__(self, db=None, verbose: bool = True):
        self.db = db
        self.verbose = verbose

        self.root_processes: dict[str, dict[str, Any]] = {}
        self.processes: dict[str, dict[str, Any]] = {}

        self.process_parameter: dict[str, list[dict[str, Any]]] = {}
        self.process_parameter_set_value: dict[str, list[dict[str, Any]]] = {}
        self.process_parameter_minmax: dict[str, list[dict[str, Any]]] = {}
        self.process_parameter_schema_table: dict[str, list[dict[str, Any]]] = {}
        self.process_parameter_permission: dict[str, list[dict[str, Any]]] = {}
        self.process_parameter_default: dict[str, list[dict[str, Any]]] = {}

    def snapshot(self) -> dict[str, Any]:
        return {
            "root_processes": self.root_processes,
            "processes": self.processes,
            "process_parameter": self.process_parameter,
            "process_parameter_set_value": self.process_parameter_set_value,
            "process_parameter_minmax": self.process_parameter_minmax,
            "process_parameter_schema_table": self.process_parameter_schema_table,
            "process_parameter_permission": self.process_parameter_permission,
            "process_parameter_default": self.process_parameter_default,
        }

    def register_from_step(self, step) -> None:
        process_id = self.PROCESS_ID_ALIASES.get(
            step.process_id,
            step.process_id,
        )

        data = dict(step.parameters)

        if process_id == "root_process":
            self.register_root_process(data)
            return

        if process_id == "process":
            self.register_process(data)
            return

        if process_id == "process_parameter":
            self.register_process_parameter(data)
            return

        if process_id == "process_parameter_set_value":
            self.register_process_parameter_set_value(data)
            return

        if process_id == "process_parameter_minmax":
            self.register_process_parameter_minmax(data)
            return

        if process_id == "process_parameter_schema_table":
            self.register_process_parameter_schema_table(data)
            return

        if process_id == "process_parameter_permission":
            self.register_process_parameter_permission(data)
            return

        if process_id == "process_parameter_default":
            self.register_process_parameter_default(data)
            return

        raise ValueError(f"Unsupported registry process_id: {process_id}")

    def register_root_process(self, data: dict[str, Any]) -> None:
        key = self._require_one(data, ["root_process", "id"])
        self.root_processes[key] = dict(data)
        self._insert_mock_or_sql("process.root_process", data)

    def register_process(self, data: dict[str, Any]) -> None:
        key = self._require_one(data, ["process", "process_id", "id"])
        self.processes[key] = dict(data)
        self._insert_mock_or_sql("process.process", data)

    def register_process_parameter(self, data: dict[str, Any]) -> None:
        self._append_by_process(self.process_parameter, data)
        self._insert_mock_or_sql("process.process_parameter", data)

    def register_process_parameter_set_value(self, data: dict[str, Any]) -> None:
        self._append_by_process(self.process_parameter_set_value, data)
        self._insert_mock_or_sql("process.process_parameter_set_value", data)

    def register_process_parameter_minmax(self, data: dict[str, Any]) -> None:
        self._append_by_process(self.process_parameter_minmax, data)
        self._insert_mock_or_sql("process.process_parameter_minmax", data)

    def register_process_parameter_schema_table(self, data: dict[str, Any]) -> None:
        self._append_by_process(self.process_parameter_schema_table, data)
        self._insert_mock_or_sql("process.process_parameter_schema_table", data)

    def register_process_parameter_permission(self, data: dict[str, Any]) -> None:
        self._append_by_process(self.process_parameter_permission, data)
        self._insert_mock_or_sql("process.process_parameter_permission", data)

    def register_process_parameter_default(self, data: dict[str, Any]) -> None:
        self._append_by_process(self.process_parameter_default, data)
        self._insert_mock_or_sql("process.process_parameter_default", data)

    def _append_by_process(
        self,
        collection: dict[str, list[dict[str, Any]]],
        data: dict[str, Any],
    ) -> None:
        process = self._require_one(data, ["process", "process_id", "id"])
        collection.setdefault(process, []).append(dict(data))

    def _require_one(self, data: dict[str, Any], keys: list[str]) -> str:
        for key in keys:
            value = data.get(key)
            if value is not None:
                return str(value)

        raise ValueError(
            "process registration requires "
            + "/".join(keys)
        )

    def _insert_mock_or_sql(self, table: str, data: dict[str, Any]) -> None:
        if self.db is None:
            self._log(f"[registry] {table}: {data}")
            return

        if getattr(self.db, "mock", True):
            self._log(f"[mock-registry] {table}: {data}")
            return

        if not data:
            raise ValueError(f"Cannot insert empty registry record into {table}")

        columns = list(data.keys())
        values = [data[column] for column in columns]

        column_sql = ", ".join(columns)
        placeholder_sql = ", ".join(["%s"] * len(values))

        sql = (
            f"INSERT INTO {table} "
            f"({column_sql}) "
            f"VALUES ({placeholder_sql});"
        )

        self.db.execute(sql, tuple(values))

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)