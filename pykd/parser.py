from __future__ import annotations

from dataclasses import dataclass

from .token import Token
from .token_type import TokenType


class ParserError(Exception):
    pass


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    data_type: str


@dataclass(frozen=True)
class CreateTableStatement:
    table_name: str
    columns: list[ColumnDefinition]


@dataclass(frozen=True)
class InsertStatement:
    table_name: str
    values: list[str]


@dataclass(frozen=True)
class SelectStatement:
    columns: list[str]
    table_name: str


@dataclass(frozen=True)
class UpdateStatement:
    table_name: str
    column: str
    value: str


@dataclass(frozen=True)
class DeleteStatement:
    table_name: str


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    def parse(self):
        token_type = self._current().type

        if token_type == TokenType.CREATE:
            return self._parse_create()

        if token_type == TokenType.INSERT:
            return self._parse_insert()

        if token_type == TokenType.SELECT:
            return self._parse_select()

        if token_type == TokenType.UPDATE:
            return self._parse_update()

        if token_type == TokenType.DELETE:
            return self._parse_delete()

        raise ParserError(
            f"Unexpected token: "
            f"{self._current().value}"
        )

    def _parse_create(self) -> CreateTableStatement:
        self._expect(TokenType.CREATE)
        self._expect(TokenType.TABLE)

        table_name = self._expect(
            TokenType.IDENTIFIER
        ).value

        self._expect(TokenType.LPAREN)

        columns = []

        while True:
            column_name = self._expect(
                TokenType.IDENTIFIER
            ).value

            data_type_token = self._current()

            if data_type_token.type not in {
                TokenType.INT,
                TokenType.TEXT,
                TokenType.BOOLEAN,
            }:
                raise ParserError(
                    "Expected column data type"
                )

            self.position += 1

            columns.append(
                ColumnDefinition(
                    column_name,
                    data_type_token.value,
                )
            )

            if self._match(TokenType.COMMA):
                continue

            break

        self._expect(TokenType.RPAREN)
        self._optional_semicolon()
        self._expect(TokenType.EOF)

        return CreateTableStatement(
            table_name,
            columns,
        )

    def _parse_insert(self) -> InsertStatement:
        self._expect(TokenType.INSERT)
        self._expect(TokenType.INTO)

        table_name = self._expect(
            TokenType.IDENTIFIER
        ).value

        self._expect(TokenType.VALUES)
        self._expect(TokenType.LPAREN)

        values = []

        while True:
            token = self._current()

            if token.type not in {
                TokenType.STRING,
                TokenType.NUMBER,
                TokenType.IDENTIFIER,
            }:
                raise ParserError(
                    "Expected a value"
                )

            values.append(token.value)
            self.position += 1

            if self._match(TokenType.COMMA):
                continue

            break

        self._expect(TokenType.RPAREN)
        self._optional_semicolon()
        self._expect(TokenType.EOF)

        return InsertStatement(
            table_name,
            values,
        )

    def _parse_select(self) -> SelectStatement:
        self._expect(TokenType.SELECT)

        columns = []

        if self._match(TokenType.STAR):
            columns.append("*")
        else:
            while True:
                columns.append(
                    self._expect(
                        TokenType.IDENTIFIER
                    ).value
                )

                if self._match(TokenType.COMMA):
                    continue

                break

        self._expect(TokenType.FROM)

        table_name = self._expect(
            TokenType.IDENTIFIER
        ).value

        self._optional_semicolon()
        self._expect(TokenType.EOF)

        return SelectStatement(
            columns,
            table_name,
        )

    def _parse_update(self) -> UpdateStatement:
        self._expect(TokenType.UPDATE)

        table_name = self._expect(
            TokenType.IDENTIFIER
        ).value

        self._expect(TokenType.SET)

        column = self._expect(
            TokenType.IDENTIFIER
        ).value

        self._expect(TokenType.EQUALS)

        token = self._current()

        if token.type not in {
            TokenType.STRING,
            TokenType.NUMBER,
            TokenType.IDENTIFIER,
        }:
            raise ParserError(
                "Expected update value"
            )

        value = token.value
        self.position += 1

        self._optional_semicolon()
        self._expect(TokenType.EOF)

        return UpdateStatement(
            table_name,
            column,
            value,
        )

    def _parse_delete(self) -> DeleteStatement:
        self._expect(TokenType.DELETE)
        self._expect(TokenType.FROM)

        table_name = self._expect(
            TokenType.IDENTIFIER
        ).value

        self._optional_semicolon()
        self._expect(TokenType.EOF)

        return DeleteStatement(
            table_name,
        )

    def _expect(self, token_type: TokenType) -> Token:
        token = self._current()

        if token.type != token_type:
            raise ParserError(
                f"Expected {token_type.name}, "
                f"got {token.type.name}"
            )

        self.position += 1

        return token

    def _match(self, token_type: TokenType) -> bool:
        if self._current().type == token_type:
            self.position += 1
            return True

        return False

    def _optional_semicolon(self) -> None:
        self._match(TokenType.SEMICOLON)

    def _current(self) -> Token:
        return self.tokens[self.position]