from pathlib import Path

import pytest

from pykd.executor import QueryExecutor
from pykd.query import (
    CreateTableQuery,
    DeleteQuery,
    InsertQuery,
    QueryError,
    SelectQuery,
    UpdateQuery,
)
from pykd.storage import StorageEngine
from pykd.table import TableManager


@pytest.fixture
def database_path(tmp_path: Path):
    return tmp_path / "query.pykd"


@pytest.fixture
def engine(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    yield engine

    engine.close()


@pytest.fixture
def executor(engine):
    return QueryExecutor(
        engine,
        TableManager(),
    )


def create_users(executor):
    executor.execute(
        CreateTableQuery(
            "users",
            [
                ("id", "INT"),
                ("name", "TEXT"),
                ("age", "INT"),
            ],
        )
    )


def test_create_table(executor):
    table = executor.execute(
        CreateTableQuery(
            "users",
            [
                ("id", "INT"),
                ("name", "TEXT"),
            ],
        )
    )

    assert table.name == "users"
    assert table.schema.column_count() == 2


def test_insert(executor):
    create_users(executor)

    result = executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    assert result.row_count == 1
    assert result.rows == [
        (1, "AK", 22)
    ]


def test_select(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    result = executor.execute(
        SelectQuery(
            "users",
            ["*"],
        )
    )

    assert result.columns == [
        "id",
        "name",
        "age",
    ]

    assert result.rows == [
        ("1", "AK", "22")
    ]


def test_select_specific_columns(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    result = executor.execute(
        SelectQuery(
            "users",
            ["name"],
        )
    )

    assert result.columns == ["name"]
    assert result.rows == [
        ("AK",)
    ]


def test_multiple_inserts(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    executor.execute(
        InsertQuery(
            "users",
            [2, "Ayush", 23],
        )
    )

    result = executor.execute(
        SelectQuery(
            "users",
            ["*"],
        )
    )

    assert result.row_count == 2


def test_update(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    result = executor.execute(
        UpdateQuery(
            "users",
            "name",
            "Ayush",
        )
    )

    assert result.rows == [(1,)]


def test_updated_value_can_be_selected(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    executor.execute(
        UpdateQuery(
            "users",
            "name",
            "Ayush",
        )
    )

    result = executor.execute(
        SelectQuery(
            "users",
            ["name"],
        )
    )

    assert result.rows == [
        ("Ayush",)
    ]


def test_delete(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    result = executor.execute(
        DeleteQuery("users")
    )

    assert result.rows == [(1,)]


def test_deleted_row_is_not_selected(executor):
    create_users(executor)

    executor.execute(
        InsertQuery(
            "users",
            [1, "AK", 22],
        )
    )

    executor.execute(
        DeleteQuery("users")
    )

    result = executor.execute(
        SelectQuery(
            "users",
            ["*"],
        )
    )

    assert result.rows == []


def test_missing_table(executor):
    with pytest.raises(QueryError):
        executor.execute(
            SelectQuery(
                "missing",
                ["*"],
            )
        )


def test_wrong_value_count(executor):
    create_users(executor)

    with pytest.raises(QueryError):
        executor.execute(
            InsertQuery(
                "users",
                [1, "AK"],
            )
        )


def test_missing_column(executor):
    create_users(executor)

    with pytest.raises(QueryError):
        executor.execute(
            SelectQuery(
                "users",
                ["email"],
            )
        )


def test_update_missing_column(executor):
    create_users(executor)

    with pytest.raises(QueryError):
        executor.execute(
            UpdateQuery(
                "users",
                "email",
                "test",
            )
        )


def test_table_requires_id_for_insert(executor):
    executor.execute(
        CreateTableQuery(
            "users",
            [
                ("name", "TEXT"),
            ],
        )
    )

    with pytest.raises(QueryError):
        executor.execute(
            InsertQuery(
                "users",
                ["AK"],
            )
        )