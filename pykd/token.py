from __future__ import annotations

from dataclasses import dataclass

from .token_type import TokenType


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int