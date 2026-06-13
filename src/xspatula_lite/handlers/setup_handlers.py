from __future__ import annotations

from typing import Any

from xspatula_lite.database import DatabaseSession
from xspatula_lite.models import ProcessStep


def sql_identifier(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("SQL identifier must be a non-empty string")
    return name.strip()


class SetupHandlers:
    """Handlers for original setup_db/delete_db process_id values."""

    def __init__(self, db: DatabaseSession):
        self.db = db

    def create_schema(self, step: ProcessStep) -> None:
        schema = sql_identifier(step.parameters["schema"])
        self.db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")

    def create_table(self, step: ProcessStep) -> None:
        p = step.parameters
        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])
        command = p.get("command", [])
        if isinstance(command, list):
            body = ",\n  ".join(command)
        elif isinstance(command, str):
            body = command
        else:
            raise ValueError("create_table command must be a list or string")

        if step.options.get("overwrite"):
            self.delete_table(step)
        self.db.execute(f"CREATE TABLE IF NOT EXISTS {schema}.{table} (\n  {body}\n);")

    def table_insert(self, step: ProcessStep) -> None:
        p = step.parameters
        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])
        command = p.get("command", {})
        columns = command.get("columns", [])
        values = command.get("values", [])
        if not columns or not isinstance(values, list):
            raise ValueError("table_insert command must contain columns and values")
        cols = ", ".join(columns)
        for row in values:
            escaped = ", ".join(self._sql_literal(v) for v in row)
            self.db.execute(f"INSERT INTO {schema}.{table} ({cols}) VALUES ({escaped});")

    def table_update(self, step: ProcessStep) -> None:
        p = step.parameters
        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])
        command = p.get("command", {})
        set_values = command.get("set") or command.get("values") or {}
        where = command.get("where", {})
        set_sql = ", ".join(f"{k} = {self._sql_literal(v)}" for k, v in set_values.items())
        where_sql = " AND ".join(f"{k} = {self._sql_literal(v)}" for k, v in where.items()) or "TRUE"
        self.db.execute(f"UPDATE {schema}.{table} SET {set_sql} WHERE {where_sql};")

    def delete_table(self, step: ProcessStep) -> None:
        p = step.parameters
        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])
        self.db.execute(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE;")

    def delete_schema(self, step: ProcessStep) -> None:
        schema = sql_identifier(step.parameters["schema"])
        self.db.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")

    def delete_database(self, step: ProcessStep) -> None:
        database = step.parameters.get("db") or step.parameters.get("database") or self.db.config.get("db")
        database = sql_identifier(database)
        self.db.execute(f"DROP DATABASE IF EXISTS {database};")

    @staticmethod
    def _sql_literal(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value).replace("'", "''")
        return f"'{text}'"
