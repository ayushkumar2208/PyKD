import pytest

from pykd.lexer import Lexer
from pykd.parser import (
    ColumnDefinition,
    CreateTableStatement,
    DeleteStatement,
    InsertStatement,
    Parser,
    ParserError,
    SelectStatement,
    UpdateStatement,
)


def parse(sql: str):
    tokens = Lexer(sql).tokenize()
    return Parser(tokens).parse()


def test_create_table():
    statement = parse(
        """
        CREATE TABLE users (
            id INT,
            name TEXT,
            age INT
        );
        """
    )

    assert isinstance(
        statement,
        CreateTableStatement,
    )

    assert statement.table_name == "users"

    assert statement.columns == [
        ColumnDefinition("id", "INT"),
        ColumnDefinition("name", "TEXT"),
        ColumnDefinition("age", "INT"),
    ]


def test_create_table_without_semicolon():
    statement = parse(
        "CREATE TABLE users (id INT)"
    )

    assert statement.table_name == "users"
    assert len(statement.columns) == 1


def test_create_table_boolean():
    statement = parse(
        """
        CREATE TABLE users (
            active BOOLEAN
        )
        """
    )

    assert statement.columns == [
        ColumnDefinition(
            "active",
            "BOOLEAN",
        )
    ]


def test_create_table_multiple_columns():
    statement = parse(
        """
        CREATE TABLE products (
            id INT,
            name TEXT,
            available BOOLEAN
        )
        """
    )

    assert len(statement.columns) == 3


def test_insert():
    statement = parse(
        "INSERT INTO users VALUES (1, 'AK');"
    )

    assert isinstance(
        statement,
        InsertStatement,
    )

    assert statement.table_name == "users"
    assert statement.values == [
        "1",
        "AK",
    ]


def test_insert_multiple_values():
    statement = parse(
        """
        INSERT INTO users
        VALUES (1, 'AK', 22);
        """
    )

    assert statement.values == [
        "1",
        "AK",
        "22",
    ]


def test_select_all():
    statement = parse(
        "SELECT * FROM users;"
    )

    assert isinstance(
        statement,
        SelectStatement,
    )

    assert statement.columns == ["*"]
    assert statement.table_name == "users"


def test_select_columns():
    statement = parse(
        "SELECT id, name FROM users;"
    )

    assert statement.columns == [
        "id",
        "name",
    ]

    assert statement.table_name == "users"


def test_update():
    statement = parse(
        "UPDATE users SET name = 'AK';"
    )

    assert isinstance(
        statement,
        UpdateStatement,
    )

    assert statement.table_name == "users"
    assert statement.column == "name"
    assert statement.value == "AK"


def test_update_number():
    statement = parse(
        "UPDATE users SET age = 22;"
    )

    assert statement.table_name == "users"
    assert statement.column == "age"
    assert statement.value == "22"


def test_delete():
    statement = parse(
        "DELETE FROM users;"
    )

    assert isinstance(
        statement,
        DeleteStatement,
    )

    assert statement.table_name == "users"


def test_invalid_statement():
    with pytest.raises(ParserError):
        parse("DROP TABLE users;")


def test_create_missing_table_keyword():
    with pytest.raises(ParserError):
        parse(
            "CREATE users (id INT);"
        )


def test_create_missing_parenthesis():
    with pytest.raises(ParserError):
        parse(
            "CREATE TABLE users id INT;"
        )


def test_create_missing_column_type():
    with pytest.raises(ParserError):
        parse(
            "CREATE TABLE users (id);"
        )


def test_create_missing_closing_parenthesis():
    with pytest.raises(ParserError):
        parse(
            "CREATE TABLE users (id INT;"
        )


def test_insert_missing_values():
    with pytest.raises(ParserError):
        parse(
            "INSERT INTO users (1, 'AK');"
        )


def test_insert_missing_parenthesis():
    with pytest.raises(ParserError):
        parse(
            "INSERT INTO users VALUES 1, 'AK';"
        )


def test_select_missing_from():
    with pytest.raises(ParserError):
        parse(
            "SELECT * users;"
        )


def test_select_missing_table():
    with pytest.raises(ParserError):
        parse(
            "SELECT * FROM;"
        )


def test_update_missing_set():
    with pytest.raises(ParserError):
        parse(
            "UPDATE users name = 'AK';"
        )


def test_update_missing_equals():
    with pytest.raises(ParserError):
        parse(
            "UPDATE users SET name 'AK';"
        )


def test_delete_missing_from():
    with pytest.raises(ParserError):
        parse(
            "DELETE users;"
        )