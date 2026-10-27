from pykd.executor import QueryExecutor
from pykd.optimizer import QueryOptimizer
from pykd.planner import QueryPlanner
from pykd.query import (
    CreateTableQuery,
    InsertQuery,
    SelectQuery,
)
from pykd.storage import StorageEngine


def test_executor_has_planner(tmp_path):
    storage = StorageEngine(tmp_path / "test.db")

    executor = QueryExecutor(storage)

    assert isinstance(
        executor.planner,
        QueryPlanner,
    )


def test_executor_has_optimizer(tmp_path):
    storage = StorageEngine(tmp_path / "test.db")

    executor = QueryExecutor(storage)

    assert isinstance(
        executor.optimizer,
        QueryOptimizer,
    )


def test_select_plan_is_generated():
    planner = QueryPlanner()

    plan = planner.plan(
        SelectQuery(
            "users",
            ["name"],
        )
    )

    assert plan.operation == "Projection"
    assert (
        plan.children[0].operation
        == "TableScan"
    )


def test_select_execution_still_works(tmp_path):
    storage = StorageEngine(
        tmp_path / "test.db"
    )
    storage.open()  # Open storage engine to allow operations

    executor = QueryExecutor(storage)

    executor.execute(
        CreateTableQuery(
            "users",
            [
                ("id", "INT"),
                ("name", "TEXT"),
            ],
        )
    )

    executor.execute(
        InsertQuery(
            "users",
            [1, "Ayush"],
        )
    )

    result = executor.execute(
        SelectQuery(
            "users",
            ["name"],
        )
    )

    assert result.columns == ["name"]
    assert result.rows == [("Ayush",)]