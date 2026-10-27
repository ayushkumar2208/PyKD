from __future__ import annotations

from dataclasses import replace

from .planner import PlanNode


class OptimizerError(Exception):
    pass


class QueryOptimizer:
    def optimize(
        self,
        plan: PlanNode,
    ) -> PlanNode:
        plan = self._merge_filters(plan)

        if plan.operation == "Filter":
            return self._optimize_filter(plan)

        children = tuple(
            self.optimize(child)
            for child in plan.children
        )

        return replace(
            plan,
            children=children,
        )

    def _optimize_filter(
        self,
        node: PlanNode,
    ) -> PlanNode:
        children = tuple(
            self.optimize(child)
            for child in node.children
        )

        node = replace(
            node,
            children=children,
        )

        if len(node.children) != 1:
            return node

        child = node.children[0]

        if child.operation != "TableScan":
            return node

        condition = node.properties.get(
            "condition"
        )

        if not self._is_indexable(condition):
            return node

        column, operator, value = condition

        return PlanNode(
            "IndexScan",
            properties={
                "table": child.properties["table"],
                "column": column,
                "operator": operator,
                "value": value,
            },
        )

    def _merge_filters(
        self,
        node: PlanNode,
    ) -> PlanNode:
        if node.operation != "Filter":
            return node

        if len(node.children) != 1:
            return node

        child = node.children[0]

        if child.operation != "Filter":
            return node

        first = child.properties.get(
            "condition"
        )
        second = node.properties.get(
            "condition"
        )

        return PlanNode(
            "Filter",
            children=child.children,
            properties={
                "condition": (
                    "AND",
                    first,
                    second,
                ),
            },
        )

    @staticmethod
    def _is_indexable(
        condition,
    ) -> bool:
        if not isinstance(
            condition,
            tuple,
        ):
            return False

        if len(condition) != 3:
            return False

        column, operator, _ = condition

        if not isinstance(column, str):
            return False

        return operator in {
            "=",
            "<",
            "<=",
            ">",
            ">=",
        }