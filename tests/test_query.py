from pykd.query import (
    CreateTableQuery,
    DeleteQuery,
    InsertQuery,
    QueryResult,
    SelectQuery,
    UpdateQuery,
)


def test_create_table_query():
    query = CreateTableQuery(
        "users",
        [
            ("id", "INT"),
            ("name", "TEXT"),
        ],
    )

    assert query.table_name == "users"
    assert len(query.columns) == 2


def test_insert_query():
    query = InsertQuery(
        "users",
        [1, "AK"],
    )

    assert query.table_name == "users"
    assert query.values == [1, "AK"]


def test_select_query():
    query = SelectQuery(
        "users",
        ["id", "name"],
    )

    assert query.table_name == "users"
    assert query.columns == ["id", "name"]


def test_select_all_query():
    query = SelectQuery(
        "users",
        ["*"],
    )

    assert query.columns == ["*"]


def test_update_query():
    query = UpdateQuery(
        "users",
        "name",
        "Ayush",
    )

    assert query.table_name == "users"
    assert query.column == "name"
    assert query.value == "Ayush"


def test_delete_query():
    query = DeleteQuery("users")

    assert query.table_name == "users"


def test_query_result():
    result = QueryResult(
        columns=["id", "name"],
        rows=[
            (1, "AK"),
            (2, "Ayush"),
        ],
    )

    assert result.row_count == 2
    assert not result.is_empty


def test_empty_query_result():
    result = QueryResult(
        columns=["id"],
        rows=[],
    )

    assert result.row_count == 0
    assert result.is_empty