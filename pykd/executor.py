from __future__ import annotations

from typing import Any

from .optimizer import QueryOptimizer
from .planner import QueryPlanner
from .query import (
    CreateTableQuery,
    DeleteQuery,
    InsertQuery,
    Query,
    QueryError,
    QueryResult,
    SelectQuery,
    UpdateQuery,
)
from .storage import StorageEngine
from .table import Column, Schema, TableError, TableManager


class QueryExecutor:
    def __init__(
        self,
        storage: StorageEngine,
        tables: TableManager | None = None,
        planner: QueryPlanner | None = None,
        optimizer: QueryOptimizer | None = None,
    ):
        self.storage = storage
        self.tables = tables or TableManager()
        self.planner = planner or QueryPlanner()
        self.optimizer = optimizer or QueryOptimizer()

    def execute(self, query: Query):
        if not isinstance(query, Query):
            raise TypeError(
                "query must be a Query"
            )

        plan = self.planner.plan(query)
        plan = self.optimizer.optimize(plan)

        try:
            if isinstance(query, CreateTableQuery):
                return self._create_table(query)

            if isinstance(query, InsertQuery):
                return self._insert(query)

            if isinstance(query, SelectQuery):
                return self._select(query)

            if isinstance(query, UpdateQuery):
                return self._update(query)

            if isinstance(query, DeleteQuery):
                return self._delete(query)

        except TableError as exc:
            raise QueryError(
                str(exc)
            ) from exc

        raise QueryError(
            f"Unsupported query type: "
            f"{type(query).__name__}"
        )

    def _create_table(
        self,
        query: CreateTableQuery,
    ):
        columns = [
            Column(name, data_type)
            for name, data_type in query.columns
        ]

        schema = Schema(columns)

        return self.tables.create(
            query.table_name,
            schema,
        )

    def _insert(
        self,
        query: InsertQuery,
    ) -> QueryResult:
        table = self.tables.get(
            query.table_name
        )

        if (
            len(query.values)
            != table.schema.column_count()
        ):
            raise QueryError(
                "Number of values does not match "
                "number of columns"
            )

        row = dict(
            zip(
                table.schema.column_names(),
                query.values,
            )
        )

        key = self._row_key(
            table.name,
            row,
        )

        value = self._serialize_row(
            table.schema.column_names(),
            row,
        )

        self.storage.put(
            key,
            value,
        )

        return QueryResult(
            columns=table.schema.column_names(),
            rows=[tuple(query.values)],
        )

    def _select(
        self,
        query: SelectQuery,
    ) -> QueryResult:
        table = self.tables.get(
            query.table_name
        )

        columns = self._resolve_columns(
            table.schema.column_names(),
            query.columns,
        )

        rows = []
        prefix = f"{table.name}:"

        for key in self.storage.keys():
            if not key.startswith(prefix):
                continue

            value = self.storage.get(key)

            if value is None:
                continue

            row = self._deserialize_row(
                table.schema.column_names(),
                value,
            )

            rows.append(
                tuple(
                    row[column]
                    for column in columns
                )
            )

        return QueryResult(
            columns=columns,
            rows=rows,
        )

    def _update(
        self,
        query: UpdateQuery,
    ) -> QueryResult:
        table = self.tables.get(
            query.table_name
        )

        column = query.column.lower()

        if not table.has_column(column):
            raise QueryError(
                f"Column not found: {column}"
            )

        updated = 0
        prefix = f"{table.name}:"

        for key in self.storage.keys():
            if not key.startswith(prefix):
                continue

            value = self.storage.get(key)

            if value is None:
                continue

            row = self._deserialize_row(
                table.schema.column_names(),
                value,
            )

            row[column] = query.value

            self.storage.put(
                key,
                self._serialize_row(
                    table.schema.column_names(),
                    row,
                ),
            )

            updated += 1

        return QueryResult(
            columns=["updated"],
            rows=[(updated,)],
        )

    def _delete(
        self,
        query: DeleteQuery,
    ) -> QueryResult:
        table = self.tables.get(
            query.table_name
        )

        deleted = 0
        prefix = f"{table.name}:"

        keys = [
            key
            for key in self.storage.keys()
            if key.startswith(prefix)
        ]

        for key in keys:
            if self.storage.delete(key):
                deleted += 1

        return QueryResult(
            columns=["deleted"],
            rows=[(deleted,)],
        )

    @staticmethod
    def _resolve_columns(
        available: list[str],
        requested: list[str],
    ) -> list[str]:
        if requested == ["*"]:
            return available

        normalized = [
            column.lower()
            for column in requested
        ]

        for column in normalized:
            if column not in available:
                raise QueryError(
                    f"Column not found: {column}"
                )

        return normalized

    @staticmethod
    def _row_key(
        table_name: str,
        row: dict[str, Any],
    ) -> str:
        if "id" not in row:
            raise QueryError(
                "Table requires an id column for now"
            )

        return f"{table_name}:{row['id']}"

    @staticmethod
    def _serialize_row(
        columns: list[str],
        row: dict[str, Any],
    ) -> str:
        return "|".join(
            str(row[column])
            for column in columns
        )

    @staticmethod
    def _deserialize_row(
        columns: list[str],
        value: str,
    ) -> dict[str, str]:
        values = value.split("|")

        if len(values) != len(columns):
            raise QueryError(
                "Stored row does not match schema"
            )

        return dict(
            zip(columns, values)
        )