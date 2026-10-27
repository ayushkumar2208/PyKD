import pytest

from pykd.table import (
    Column,
    Schema,
    Table,
    TableError,
    TableManager,
)


def test_column_creation():
    column = Column("name", "text")

    assert column.name == "name"
    assert column.data_type == "TEXT"
    assert column.nullable


def test_column_normalizes_name():
    column = Column("UserName", "text")

    assert column.name == "username"


def test_column_normalizes_type():
    column = Column("age", "int")

    assert column.data_type == "INT"


def test_empty_column_name():
    with pytest.raises(ValueError):
        Column("", "TEXT")


def test_empty_column_type():
    with pytest.raises(ValueError):
        Column("name", "")


def test_schema_creation():
    schema = Schema([
        Column("id", "INT"),
        Column("name", "TEXT"),
    ])

    assert schema.column_count() == 2


def test_schema_column_names():
    schema = Schema([
        Column("id", "INT"),
        Column("name", "TEXT"),
    ])

    assert schema.column_names() == [
        "id",
        "name",
    ]


def test_schema_has_column():
    schema = Schema([
        Column("id", "INT"),
    ])

    assert schema.has_column("id")
    assert not schema.has_column("name")


def test_schema_get_column():
    schema = Schema([
        Column("id", "INT"),
    ])

    column = schema.get_column("id")

    assert column.data_type == "INT"


def test_schema_missing_column():
    schema = Schema()

    with pytest.raises(TableError):
        schema.get_column("missing")


def test_duplicate_columns():
    with pytest.raises(TableError):
        Schema([
            Column("id", "INT"),
            Column("id", "TEXT"),
        ])


def test_add_column():
    schema = Schema()

    schema.add_column(
        Column("id", "INT")
    )

    assert schema.has_column("id")


def test_duplicate_add_column():
    schema = Schema([
        Column("id", "INT"),
    ])

    with pytest.raises(TableError):
        schema.add_column(
            Column("id", "TEXT")
        )


def test_table_creation():
    schema = Schema([
        Column("id", "INT"),
        Column("name", "TEXT"),
    ])

    table = Table("users", schema)

    assert table.name == "users"
    assert table.schema == schema


def test_table_name_normalization():
    table = Table(
        "USERS",
        Schema(),
    )

    assert table.name == "users"


def test_table_has_column():
    table = Table(
        "users",
        Schema([
            Column("id", "INT"),
        ]),
    )

    assert table.has_column("id")


def test_table_get_column():
    table = Table(
        "users",
        Schema([
            Column("id", "INT"),
        ]),
    )

    assert table.get_column("id").data_type == "INT"


def test_table_manager_create():
    manager = TableManager()

    table = manager.create(
        "users",
        Schema([
            Column("id", "INT"),
        ]),
    )

    assert table.name == "users"
    assert manager.exists("users")
    assert manager.count() == 1


def test_table_manager_get():
    manager = TableManager()

    manager.create(
        "users",
        Schema(),
    )

    table = manager.get("users")

    assert table.name == "users"


def test_table_manager_missing_table():
    manager = TableManager()

    with pytest.raises(TableError):
        manager.get("users")


def test_table_manager_duplicate_table():
    manager = TableManager()

    manager.create(
        "users",
        Schema(),
    )

    with pytest.raises(TableError):
        manager.create(
            "users",
            Schema(),
        )


def test_table_manager_drop():
    manager = TableManager()

    manager.create(
        "users",
        Schema(),
    )

    assert manager.drop("users")
    assert not manager.exists("users")


def test_table_manager_drop_missing():
    manager = TableManager()

    assert not manager.drop("missing")


def test_table_manager_names():
    manager = TableManager()

    manager.create("users", Schema())
    manager.create("orders", Schema())

    assert set(manager.names()) == {
        "users",
        "orders",
    }


def test_table_manager_clear():
    manager = TableManager()

    manager.create("users", Schema())
    manager.create("orders", Schema())

    manager.clear()

    assert manager.count() == 0
    assert manager.names() == []


def test_invalid_table_name():
    manager = TableManager()

    with pytest.raises(ValueError):
        manager.create("", Schema())