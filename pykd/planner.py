from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .query import (
    CreateTableQuery,
    DeleteQuery,
    InsertQuery,
    SelectQuery,
    UpdateQuery,
)


class PlannerError(Exception):
    pass


@dataclass(frozen=True)
class PlanNode:
    operation: str
    children: tuple["PlanNode", ...] = ()
    properties: dict[str, Any] | None = None

    def __post_init__(self):
        if self.properties is None:
            object.__setattr__(
                self,
                "properties",
                {},
            )


class QueryPlanner:
    def plan(self, query: Any) -> PlanNode:
        q_type = type(query).__name__

        if isinstance(query, CreateTableQuery) or q_type == "CreateTableQuery":
            return self._create_table(query)

        if isinstance(query, SelectQuery) or q_type == "SelectQuery":
            return self._select(query)

        if isinstance(query, InsertQuery) or q_type == "InsertQuery":
            return self._insert(query)

        if isinstance(query, UpdateQuery) or q_type == "UpdateQuery":
            return self._update(query)

        if isinstance(query, DeleteQuery) or q_type == "DeleteQuery":
            return self._delete(query)

        raise PlannerError(
            f"Unsupported query type: "
            f"{q_type}"
        )

    def _create_table(
        self,
        query: CreateTableQuery,
    ) -> PlanNode:
        return PlanNode(
            "CreateTable",
            properties={
                "table": query.table_name,
                "columns": tuple(query.columns),
            },
        )

    def _select(
        self,
        query: SelectQuery,
    ) -> PlanNode:
        scan = PlanNode(
            "TableScan",
            properties={
                "table": query.table_name,
            },
        )

        node = scan

        if getattr(query, "where", None) is not None:
            node = PlanNode(
                "Filter",
                children=(node,),
                properties={
                    "condition": query.where,
                },
            )

        return PlanNode(
            "Projection",
            children=(node,),
            properties={
                "columns": tuple(query.columns),
            },
        )

    def _insert(
        self,
        query: InsertQuery,
    ) -> PlanNode:
        return PlanNode(
            "Insert",
            properties={
                "table": query.table_name,
                "values": tuple(query.values),
            },
        )

    def _update(
        self,
        query: UpdateQuery,
    ) -> PlanNode:
        scan = PlanNode(
            "TableScan",
            properties={
                "table": query.table_name,
            },
        )

        node = scan

        if getattr(query, "where", None) is not None:
            node = PlanNode(
                "Filter",
                children=(node,),
                properties={
                    "condition": query.where,
                },
            )

        return PlanNode(
            "Update",
            children=(node,),
            properties={
                "table": query.table_name,
                "assignments": getattr(query, "assignments", {}),
            },
        )

    def _delete(
        self,
        query: DeleteQuery,
    ) -> PlanNode:
        scan = PlanNode(
            "TableScan",
            properties={
                "table": query.table_name,
            },
        )

        node = scan

        if getattr(query, "where", None) is not None:
            node = PlanNode(
                "Filter",
                children=(node,),
                properties={
                    "condition": query.where,
                },
            )

        return PlanNode(
            "Delete",
            children=(node,),
            properties={
                "table": query.table_name,
            },
        )