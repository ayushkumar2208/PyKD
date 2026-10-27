from __future__ import annotations

from dataclasses import dataclass, field


class TableError(Exception):
    pass


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    nullable: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("Column name must be a string")

        if not self.name:
            raise ValueError("Column name cannot be empty")

        if not isinstance(self.data_type, str):
            raise TypeError("Data type must be a string")

        if not self.data_type:
            raise ValueError("Data type cannot be empty")

        object.__setattr__(
            self,
            "name",
            self.name.lower(),
        )

        object.__setattr__(
            self,
            "data_type",
            self.data_type.upper(),
        )


@dataclass
class Schema:
    columns: list[Column] = field(default_factory=list)

    def __post_init__(self) -> None:
        names = set()

        for column in self.columns:
            if column.name in names:
                raise TableError(
                    f"Duplicate column: {column.name}"
                )

            names.add(column.name)

    def add_column(self, column: Column) -> None:
        if self.has_column(column.name):
            raise TableError(
                f"Duplicate column: {column.name}"
            )

        self.columns.append(column)

    def get_column(self, name: str) -> Column:
        name = name.lower()

        for column in self.columns:
            if column.name == name:
                return column

        raise TableError(
            f"Column not found: {name}"
        )

    def has_column(self, name: str) -> bool:
        name = name.lower()

        return any(
            column.name == name
            for column in self.columns
        )

    def column_names(self) -> list[str]:
        return [
            column.name
            for column in self.columns
        ]

    def column_count(self) -> int:
        return len(self.columns)


@dataclass
class Table:
    name: str
    schema: Schema

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("Table name must be a string")

        if not self.name:
            raise ValueError(
                "Table name cannot be empty"
            )

        if not isinstance(self.schema, Schema):
            raise TypeError(
                "schema must be a Schema"
            )

        self.name = self.name.lower()

    def has_column(self, name: str) -> bool:
        return self.schema.has_column(name)

    def get_column(self, name: str) -> Column:
        return self.schema.get_column(name)


class TableManager:
    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    def create(
        self,
        name: str,
        schema: Schema,
    ) -> Table:
        name = self._normalize_name(name)

        if name in self._tables:
            raise TableError(
                f"Table already exists: {name}"
            )

        table = Table(name, schema)
        self._tables[name] = table

        return table

    def get(self, name: str) -> Table:
        name = self._normalize_name(name)

        try:
            return self._tables[name]
        except KeyError as exc:
            raise TableError(
                f"Table not found: {name}"
            ) from exc

    def drop(self, name: str) -> bool:
        name = self._normalize_name(name)

        if name not in self._tables:
            return False

        del self._tables[name]

        return True

    def exists(self, name: str) -> bool:
        name = self._normalize_name(name)

        return name in self._tables

    def names(self) -> list[str]:
        return list(self._tables.keys())

    def count(self) -> int:
        return len(self._tables)

    def clear(self) -> None:
        self._tables.clear()

    @staticmethod
    def _normalize_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError(
                "Table name must be a string"
            )

        if not name:
            raise ValueError(
                "Table name cannot be empty"
            )

        return name.lower()