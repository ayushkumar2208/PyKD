from __future__ import annotations

from .token import Token
from .token_type import TokenType


class LexerError(Exception):
    pass


class Lexer:
    KEYWORDS = {
        "CREATE": TokenType.CREATE,
        "TABLE": TokenType.TABLE,
        "INSERT": TokenType.INSERT,
        "INTO": TokenType.INTO,
        "VALUES": TokenType.VALUES,
        "SELECT": TokenType.SELECT,
        "FROM": TokenType.FROM,
        "UPDATE": TokenType.UPDATE,
        "SET": TokenType.SET,
        "DELETE": TokenType.DELETE,
        "WHERE": TokenType.WHERE,
        "INT": TokenType.INT,
        "TEXT": TokenType.TEXT,
        "BOOLEAN": TokenType.BOOLEAN,
    }

    SIMPLE_TOKENS = {
        "*": TokenType.STAR,
        ",": TokenType.COMMA,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "=": TokenType.EQUALS,
        ";": TokenType.SEMICOLON,
    }

    def __init__(self, sql: str):
        if not isinstance(sql, str):
            raise TypeError("SQL must be a string")

        self.sql = sql
        self.position = 0
        self.length = len(sql)

    def tokenize(self) -> list[Token]:
        tokens = []

        while not self._at_end():
            self._skip_whitespace()

            if self._at_end():
                break

            char = self._current()

            if char in self.SIMPLE_TOKENS:
                tokens.append(
                    Token(
                        self.SIMPLE_TOKENS[char],
                        char,
                        self.position,
                    )
                )
                self.position += 1
                continue

            if char in ("'", '"'):
                tokens.append(self._read_string())
                continue

            if char.isdigit():
                tokens.append(self._read_number())
                continue

            if char.isalpha() or char == "_":
                tokens.append(self._read_identifier())
                continue

            raise LexerError(
                f"Unexpected character '{char}' "
                f"at position {self.position}"
            )

        tokens.append(
            Token(
                TokenType.EOF,
                "",
                self.position,
            )
        )

        return tokens

    def _read_identifier(self) -> Token:
        start = self.position

        while not self._at_end():
            char = self._current()

            if not (
                char.isalnum() or char == "_"
            ):
                break

            self.position += 1

        value = self.sql[start:self.position]
        upper = value.upper()

        token_type = self.KEYWORDS.get(
            upper,
            TokenType.IDENTIFIER,
        )

        return Token(
            token_type,
            value,
            start,
        )

    def _read_number(self) -> Token:
        start = self.position

        while not self._at_end():
            if not self._current().isdigit():
                break

            self.position += 1

        value = self.sql[start:self.position]

        return Token(
            TokenType.NUMBER,
            value,
            start,
        )

    def _read_string(self) -> Token:
        quote = self._current()
        start = self.position

        self.position += 1
        chars = []

        while not self._at_end():
            char = self._current()

            if char == quote:
                self.position += 1

                return Token(
                    TokenType.STRING,
                    "".join(chars),
                    start,
                )

            if char == "\\":
                self.position += 1

                if self._at_end():
                    raise LexerError(
                        "Unterminated string"
                    )

                escaped = self._current()

                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                }

                chars.append(
                    escape_map.get(
                        escaped,
                        escaped,
                    )
                )

                self.position += 1
                continue

            chars.append(char)
            self.position += 1

        raise LexerError(
            f"Unterminated string at position {start}"
        )

    def _skip_whitespace(self) -> None:
        while not self._at_end():
            if not self._current().isspace():
                break

            self.position += 1

    def _current(self) -> str:
        return self.sql[self.position]

    def _at_end(self) -> bool:
        return self.position >= self.length