from dataclasses import dataclass

import pytest

from pykd.planner import (
    PlanNode,
    PlannerError,
    QueryPlanner,
)


@dataclass
class SelectQuery:
    table_name: str
    columns: list[str]
    where: object = None


@dataclass
class InsertQuery:
    table_name: str
    values: tuple


@dataclass
class UpdateQuery:
    table_name: str
    assignments: dict
    where: object = None


@dataclass
class DeleteQuery:
    table_name: str
    where: object = None


def test_select_plan():
    planner = QueryPlanner()

    plan = planner.plan(
        SelectQuery(
            "users",
            ["name", "age"],
        )
    )

    assert plan.operation == "Projection"
    assert plan.properties["columns"] == (
        "name",
        "age",
    )

    assert (
        plan.children[0].operation
        == "TableScan"
    )


def test_select_with_filter():
    planner = QueryPlanner()

    condition = ("age", ">", 20)

    plan = planner.plan(
        SelectQuery(
            "users",
            ["name"],
            condition,
        )
    )

    assert plan.operation == "Projection"

    filter_node = plan.children[0]

    assert filter_node.operation == "Filter"
    assert (
        filter_node.properties["condition"]
        == condition
    )

    assert (
        filter_node.children[0].operation
        == "TableScan"
    )


def test_insert_plan():
    planner = QueryPlanner()

    plan = planner.plan(
        InsertQuery(
            "users",
            ("Ayush", 21),
        )
    )

    assert plan.operation == "Insert"
    assert plan.properties["table"] == "users"


def test_update_plan():
    planner = QueryPlanner()

    plan = planner.plan(
        UpdateQuery(
            "users",
            {"age": 22},
        )
    )

    assert plan.operation == "Update"
    assert (
        plan.children[0].operation
        == "TableScan"
    )


def test_update_with_filter():
    planner = QueryPlanner()

    plan = planner.plan(
        UpdateQuery(
            "users",
            {"age": 22},
            ("id", "=", 1),
        )
    )

    assert plan.operation == "Update"
    assert (
        plan.children[0].operation
        == "Filter"
    )


def test_delete_plan():
    planner = QueryPlanner()

    plan = planner.plan(
        DeleteQuery("users")
    )

    assert plan.operation == "Delete"
    assert (
        plan.children[0].operation
        == "TableScan"
    )


def test_delete_with_filter():
    planner = QueryPlanner()

    plan = planner.plan(
        DeleteQuery(
            "users",
            ("id", "=", 1),
        )
    )

    assert plan.operation == "Delete"
    assert (
        plan.children[0].operation
        == "Filter"
    )


def test_unknown_query():
    planner = QueryPlanner()

    class UnknownQuery:
        pass

    with pytest.raises(PlannerError):
        planner.plan(UnknownQuery())


def test_plan_node_defaults():
    node = PlanNode("TableScan")

    assert node.children == ()
    assert node.properties == {}