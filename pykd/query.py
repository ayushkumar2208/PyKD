from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class QueryError(Exception):
    pass


@dataclass(frozen=True)
class Query:
    pass


@dataclass(frozen=True)
class CreateTableQuery(Query):
    table_name: str
    columns: list[tuple[str, str]]


@dataclass(frozen=True)
class InsertQuery(Query):
    table_name: str
    values: list[Any]


@dataclass(frozen=True)
class SelectQuery(Query):
    table_name: str
    columns: list[str]
    where: Any | None = None


@dataclass(frozen=True)
class UpdateQuery(Query):
    table_name: str
    column: str
    value: Any
    where: Any | None = None
    assignments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeleteQuery(Query):
    table_name: str
    where: Any | None = None


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def is_empty(self) -> bool:
        return not self.rows