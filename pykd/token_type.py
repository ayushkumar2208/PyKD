from enum import Enum, auto


class TokenType(Enum):
    CREATE = auto()
    TABLE = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    SELECT = auto()
    FROM = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    WHERE = auto()

    INT = auto()
    TEXT = auto()
    BOOLEAN = auto()

    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    STAR = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    EQUALS = auto()
    SEMICOLON = auto()

    EOF = auto()