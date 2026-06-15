from __future__ import annotations

from typing import Any


class DatabaseSession:
    def __init__(
        self,
        config: dict[str, Any] | None = None,
        mock: bool | None = None,
        verbose: int | bool = 1,
    ):
        self.config = config or {"type": "mock"}
        self.verbose = verbose

        self.connection = None

        self.executed_sql: list[str] = []
        self.executed = self.executed_sql

        db_type = (
            self.config.get("type")
            or self.config.get("engine")
            or self.config.get("db_type")
        )

        if mock is None:
            self.mock = db_type in (None, "mock")
        else:
            self.mock = mock

    def connect(self) -> None:
        if self.mock:
            self._log("[mock-db] connect")
            return

        db_type = (
            self.config.get("type")
            or self.config.get("engine")
            or self.config.get("db_type")
        )

        if db_type not in ("postgres", "postgresql"):
            raise ValueError(
                f"Unsupported database type: {db_type}"
            )

        try:
            import psycopg
        except ImportError as error:
            raise ImportError(
                "PostgreSQL support requires psycopg. "
                "Install with: pip install psycopg[binary]"
            ) from error
        if self.config.get("auto_create", False):
            self.create_database_if_missing()
        self.connection = psycopg.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 5432),
            dbname=(
                self.config.get("db")
                or self.config.get("database")
                or self.config.get("name")
            ),
            user=(
                self.config.get("user")
                or self.config.get("user_name")
                or self.config.get("username")
            ),
            password=self.config.get("password", ""),
        )

        self._log("[postgres-db] connect")

    def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> None:
        if self.mock:
            self.executed_sql.append(sql)
            self._log(f"[mock-sql] {sql}")
            return

        if self.connection is None:
            self.connect()

        assert self.connection is not None

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)

        self.connection.commit()

        self._log(f"[postgres-sql] {sql}")

    def execute_many(
        self,
        sql: str,
        rows: list[tuple[Any, ...]],
    ) -> None:
        if self.mock:
            for row in rows:
                self.executed_sql.append(sql)
                self._log(f"[mock-sql] {sql} {row}")
            return

        if self.connection is None:
            self.connect()

        assert self.connection is not None

        with self.connection.cursor() as cursor:
            cursor.executemany(sql, rows)

        self.connection.commit()

        self._log(f"[postgres-sql-many] {sql}")

    def create_database_if_missing(self) -> None:
        if self.mock:
            dbname = (
                self.config.get("db")
                or self.config.get("database")
                or self.config.get("name")
            )
            self._log(f"[mock-db] CREATE DATABASE IF NOT EXISTS {dbname}")
            return

        dbname = (
            self.config.get("db")
            or self.config.get("database")
            or self.config.get("name")
        )

        if not dbname:
            raise ValueError("Database name is required")

        try:
            import psycopg
            from psycopg import sql
        except ImportError as error:
            raise ImportError(
                "PostgreSQL support requires psycopg. "
                "Install with: pip install psycopg[binary]"
            ) from error

        admin_db = self.config.get("admin_db", "postgres")

        conn = psycopg.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 5432),
            dbname=admin_db,
            user=(
                self.config.get("user")
                or self.config.get("user_name")
                or self.config.get("username")
            ),
            password=self.config.get("password", ""),
            autocommit=True,
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;",
                    (dbname,),
                )

                exists = cursor.fetchone() is not None

                if exists:
                    self._log(f"[postgres-db] database exists: {dbname}")
                    return

                cursor.execute(
                    sql.SQL("CREATE DATABASE {};").format(
                        sql.Identifier(dbname)
                    )
                )

                self._log(f"[postgres-db] created database: {dbname}")

        finally:
            conn.close()
    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self._log("[postgres-db] close")

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)
