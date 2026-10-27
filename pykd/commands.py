from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    SET = "SET"
    GET = "GET"
    DELETE = "DELETE"
    EXISTS = "EXISTS"
    KEYS = "KEYS"
    CLEAR = "CLEAR"
    SYNC = "SYNC"
    HELP = "HELP"
    EXIT = "EXIT"


@dataclass(frozen=True)
class Command:
    type: CommandType
    key: str | None = None
    value: str | None = None


class CommandError(Exception):
    pass


def parse_command(line: str) -> Command:
    line = line.strip()

    if not line:
        raise CommandError("Empty command")

    parts = line.split(maxsplit=2)
    command = parts[0].upper()

    try:
        command_type = CommandType(command)
    except ValueError as exc:
        raise CommandError(
            f"Unknown command: {parts[0]}"
        ) from exc

    if command_type == CommandType.SET:
        if len(parts) < 3:
            raise CommandError(
                "Usage: SET <key> <value>"
            )

        return Command(
            type=CommandType.SET,
            key=parts[1],
            value=parts[2],
        )

    if command_type in {
        CommandType.GET,
        CommandType.DELETE,
        CommandType.EXISTS,
    }:
        if len(parts) != 2:
            raise CommandError(
                f"Usage: {command_type.value} <key>"
            )

        return Command(
            type=command_type,
            key=parts[1],
        )

    if command_type in {
        CommandType.KEYS,
        CommandType.CLEAR,
        CommandType.SYNC,
        CommandType.HELP,
        CommandType.EXIT,
    }:
        if len(parts) != 1:
            raise CommandError(
                f"{command_type.value} does not accept arguments"
            )

        return Command(type=command_type)

    raise CommandError(
        f"Unsupported command: {command_type.value}"
    )