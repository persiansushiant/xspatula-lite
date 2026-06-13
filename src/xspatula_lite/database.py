from __future__ import annotations

from typing import Any


class DatabaseSession:
    """Small DB facade with mock-first behavior.

    Later, a psycopg2 connection can be injected without changing loaders,
    dispatcher, pilots, or handlers.
    """

    def __init__(self, config: dict[str, Any] | None = None, *, mock: bool = True, verbose: int = 1):
        self.config = config or {}
        self.mock = mock
        self.verbose = verbose
        self.connection = None
        self.executed: list[str] = []

    def connect(self) -> None:
        if self.mock:
            self.log("[mock-db] connect", level=1)
            return
        raise NotImplementedError("Real PostgreSQL connection is not implemented yet. Use mock=True.")

    def execute(self, sql: str, *, commit: bool = True) -> None:
        self.executed.append(sql)
        if self.mock:
            self.log(f"[mock-sql] {sql}", level=1)
            return
        raise NotImplementedError("Real SQL execution is not implemented yet. Use mock=True.")

    def close(self) -> None:
        if self.mock:
            self.log("[mock-db] close", level=2)
            return

    def log(self, message: str, *, level: int = 1) -> None:
        if self.verbose >= level:
            print(message)
