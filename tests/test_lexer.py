import pytest

from pykd.lexer import Lexer, LexerError
from pykd.token_type import TokenType


def test_create_table_tokens():
    sql = """
    CREATE TABLE users (
        id INT,
        name TEXT
    );
    """

    tokens = Lexer(sql).tokenize()

    types = [token.type for token in tokens]

    assert types == [
        TokenType.CREATE,
        TokenType.TABLE,
        TokenType.IDENTIFIER,
        TokenType.LPAREN,
        TokenType.IDENTIFIER,
        TokenType.INT,
        TokenType.COMMA,
        TokenType.IDENTIFIER,
        TokenType.TEXT,
        TokenType.RPAREN,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]


def test_keywords_are_case_insensitive():
    tokens = Lexer(
        "create table users"
    ).tokenize()

    assert tokens[0].type == TokenType.CREATE
    assert tokens[1].type == TokenType.TABLE


def test_identifier():
    tokens = Lexer(
        "users"
    ).tokenize()

    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "users"


def test_number():
    tokens = Lexer(
        "123"
    ).tokenize()

    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == "123"


def test_string():
    tokens = Lexer(
        "'hello'"
    ).tokenize()

    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello"


def test_double_quoted_string():
    tokens = Lexer(
        '"hello"'
    ).tokenize()

    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello"


def test_string_with_spaces():
    tokens = Lexer(
        "'hello world'"
    ).tokenize()

    assert tokens[0].value == "hello world"


def test_string_escape():
    tokens = Lexer(
        r"'hello\nworld'"
    ).tokenize()

    assert tokens[0].value == "hello\nworld"


def test_symbols():
    tokens = Lexer(
        "*,()=;"
    ).tokenize()

    assert [
        token.type
        for token in tokens[:-1]
    ] == [
        TokenType.STAR,
        TokenType.COMMA,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.EQUALS,
        TokenType.SEMICOLON,
    ]


def test_insert_tokens():
    tokens = Lexer(
        "INSERT INTO users VALUES (1, 'AK');"
    ).tokenize()

    assert tokens[0].type == TokenType.INSERT
    assert tokens[1].type == TokenType.INTO
    assert tokens[2].type == TokenType.IDENTIFIER
    assert tokens[3].type == TokenType.VALUES


def test_select_tokens():
    tokens = Lexer(
        "SELECT * FROM users;"
    ).tokenize()

    assert tokens[0].type == TokenType.SELECT
    assert tokens[1].type == TokenType.STAR
    assert tokens[2].type == TokenType.FROM


def test_update_tokens():
    tokens = Lexer(
        "UPDATE users SET name = 'AK';"
    ).tokenize()

    assert tokens[0].type == TokenType.UPDATE
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.SET
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[4].type == TokenType.EQUALS


def test_delete_tokens():
    tokens = Lexer(
        "DELETE FROM users;"
    ).tokenize()

    assert tokens[0].type == TokenType.DELETE
    assert tokens[1].type == TokenType.FROM


def test_eof_token():
    tokens = Lexer("SELECT").tokenize()

    assert tokens[-1].type == TokenType.EOF


def test_whitespace_is_ignored():
    tokens = Lexer(
        "   SELECT   *   FROM   users   "
    ).tokenize()

    assert tokens[0].type == TokenType.SELECT
    assert tokens[1].type == TokenType.STAR
    assert tokens[2].type == TokenType.FROM


def test_invalid_character():
    with pytest.raises(LexerError):
        Lexer("SELECT @").tokenize()


def test_unterminated_string():
    with pytest.raises(LexerError):
        Lexer("'hello").tokenize()


def test_backslash_at_end_of_string():
    with pytest.raises(LexerError):
        Lexer("'hello\\").tokenize()


def test_empty_sql():
    tokens = Lexer("").tokenize()

    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF