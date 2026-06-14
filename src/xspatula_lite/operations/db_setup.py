from __future__ import annotations

from typing import Any

from xspatula_lite.models import ProcessStep


def sql_identifier(value: str) -> str:
    if not value:
        raise ValueError("SQL identifier cannot be empty")

    value = str(value)

    allowed = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_"
    )

    if not all(char in allowed for char in value):
        raise ValueError(f"Unsafe SQL identifier: {value}")

    return value


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    if isinstance(value, (int, float)):
        return str(value)

    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


class SetupHandlers:
    def __init__(self, db):
        self.db = db

    def create_schema(self, step: ProcessStep) -> None:
        p = step.parameters
        schema = sql_identifier(p["schema"])

        sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"

        self.db.execute(sql)

    def create_table(self, step: ProcessStep) -> None:
        p = step.parameters

        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])

        command = p.get("command", [])

        if not isinstance(command, list) or not command:
            raise ValueError(
                "create_table parameters.command must be a non-empty list"
            )

        column_sql = ",\n  ".join(command)

        sql = (
            f"CREATE TABLE IF NOT EXISTS {schema}.{table} "
            f"(\n  {column_sql}\n);"
        )

        self.db.execute(sql)

    def table_insert(self, step: ProcessStep) -> None:
        p = step.parameters

        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])

        command = p.get("command", {})

        if not isinstance(command, dict):
            raise ValueError(
                "table_insert parameters.command must be an object"
            )

        columns = command.get("columns", [])
        values = command.get("values", [])

        if not columns or not isinstance(columns, list):
            raise ValueError("table_insert command must contain columns")

        if not values or not isinstance(values, list):
            raise ValueError("table_insert command must contain values")

        safe_columns = [
            sql_identifier(column)
            for column in columns
        ]

        cols = ", ".join(safe_columns)

        for row in values:
            if not isinstance(row, list):
                raise ValueError(
                    "table_insert each value row must be a list"
                )

            if len(row) != len(columns):
                raise ValueError(
                    "table_insert row length must match columns length"
                )

            row_sql = ", ".join(
                sql_literal(value)
                for value in row
            )

            sql = (
                f"INSERT INTO {schema}.{table} "
                f"({cols}) "
                f"VALUES ({row_sql});"
            )

            self.db.execute(sql)

    def table_update(self, step: ProcessStep) -> None:
        p = step.parameters

        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])

        command = p.get("command", {})

        if not isinstance(command, dict):
            raise ValueError(
                "table_update parameters.command must be an object"
            )

        set_values = command.get("set", {})
        where_values = command.get("where", {})

        if not set_values or not isinstance(set_values, dict):
            raise ValueError(
                "table_update command must contain set object"
            )

        set_sql = ", ".join(
            f"{sql_identifier(column)} = {sql_literal(value)}"
            for column, value in set_values.items()
        )

        sql = f"UPDATE {schema}.{table} SET {set_sql}"

        if where_values:
            if not isinstance(where_values, dict):
                raise ValueError(
                    "table_update command.where must be an object"
                )

            where_sql = " AND ".join(
                f"{sql_identifier(column)} = {sql_literal(value)}"
                for column, value in where_values.items()
            )

            sql += f" WHERE {where_sql}"

        sql += ";"

        self.db.execute(sql)

    def delete_table(self, step: ProcessStep) -> None:
        p = step.parameters

        schema = sql_identifier(p["schema"])
        table = sql_identifier(p["table"])

        sql = f"DROP TABLE IF EXISTS {schema}.{table};"

        self.db.execute(sql)

    def delete_schema(self, step: ProcessStep) -> None:
        p = step.parameters

        schema = sql_identifier(p["schema"])
        cascade = bool(p.get("cascade", True))

        if cascade:
            sql = f"DROP SCHEMA IF EXISTS {schema} CASCADE;"
        else:
            sql = f"DROP SCHEMA IF EXISTS {schema};"

        self.db.execute(sql)

    def delete_database(self, step: ProcessStep) -> None:
        p = step.parameters

        database = sql_identifier(
            p.get("database")
            or p.get("db")
            or p.get("name")
        )

        sql = f"DROP DATABASE IF EXISTS {database};"

        self.db.execute(sql)

    def grant(self, step: ProcessStep) -> None:
        p = step.parameters
        command = p.get("command", [])

        if not isinstance(command, list):
            raise ValueError("grant parameters.command must be a list")

        for statement in command:
            stmt = str(statement).strip()

            if not stmt.upper().startswith(("GRANT ", "REVOKE ")):
                raise ValueError(
                    "grant only accepts GRANT/REVOKE statements"
                )

            if stmt.rstrip(";").count(";") > 0:
                raise ValueError(
                    "grant does not allow stacked SQL statements"
                )

            if not stmt.endswith(";"):
                stmt += ";"

            self.db.execute(stmt)