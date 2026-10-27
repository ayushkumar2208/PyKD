from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum


class RecordType(IntEnum):
    SET = 1
    DELETE = 2


RECORD_HEADER_FORMAT = ">BII"
RECORD_HEADER_SIZE = struct.calcsize(RECORD_HEADER_FORMAT)

MAX_KEY_SIZE = 1024
MAX_VALUE_SIZE = 1024 * 1024


class RecordError(Exception):
    pass


@dataclass(frozen=True)
class Record:
    key: str
    value: str = ""
    record_type: RecordType = RecordType.SET

    def __post_init__(self) -> None:
        if not isinstance(self.key, str):
            raise TypeError("Record key must be a string")

        if not isinstance(self.value, str):
            raise TypeError("Record value must be a string")

        if not isinstance(self.record_type, RecordType):
            raise TypeError("Invalid record type")

        if not self.key:
            raise ValueError("Record key cannot be empty")

        if "\x00" in self.key:
            raise ValueError(
                "Record key contains a null character"
            )

        key_size = len(self.key_bytes)
        value_size = len(self.value_bytes)

        if key_size > MAX_KEY_SIZE:
            raise RecordError(
                f"Key exceeds maximum size of {MAX_KEY_SIZE} bytes"
            )

        if value_size > MAX_VALUE_SIZE:
            raise RecordError(
                f"Value exceeds maximum size of {MAX_VALUE_SIZE} bytes"
            )

        if (
            self.record_type == RecordType.DELETE
            and self.value
        ):
            raise ValueError(
                "DELETE records cannot contain a value"
            )

    @property
    def key_bytes(self) -> bytes:
        return self.key.encode("utf-8")

    @property
    def value_bytes(self) -> bytes:
        return self.value.encode("utf-8")

    @property
    def serialized_size(self) -> int:
        return (
            RECORD_HEADER_SIZE
            + len(self.key_bytes)
            + len(self.value_bytes)
        )

    @property
    def is_delete(self) -> bool:
        return self.record_type == RecordType.DELETE

    @property
    def is_set(self) -> bool:
        return self.record_type == RecordType.SET

    def serialize(self) -> bytes:
        key_data = self.key_bytes
        value_data = self.value_bytes

        header = struct.pack(
            RECORD_HEADER_FORMAT,
            int(self.record_type),
            len(key_data),
            len(value_data),
        )

        return header + key_data + value_data

    @classmethod
    def deserialize(cls, data: bytes) -> Record:
        if len(data) < RECORD_HEADER_SIZE:
            raise RecordError(
                "Record data is too small"
            )

        (
            record_type,
            key_size,
            value_size,
        ) = struct.unpack(
            RECORD_HEADER_FORMAT,
            data[:RECORD_HEADER_SIZE],
        )

        try:
            record_type = RecordType(record_type)
        except ValueError as exc:
            raise RecordError(
                f"Unknown record type: {record_type}"
            ) from exc

        if key_size > MAX_KEY_SIZE:
            raise RecordError("Invalid key size")

        if value_size > MAX_VALUE_SIZE:
            raise RecordError("Invalid value size")

        if (
            record_type == RecordType.DELETE
            and value_size != 0
        ):
            raise RecordError(
                "DELETE record cannot contain a value"
            )

        expected_size = (
            RECORD_HEADER_SIZE
            + key_size
            + value_size
        )

        if len(data) != expected_size:
            raise RecordError(
                f"Invalid record size: expected "
                f"{expected_size}, got {len(data)}"
            )

        key_start = RECORD_HEADER_SIZE
        key_end = key_start + key_size
        value_end = key_end + value_size

        key_data = data[key_start:key_end]
        value_data = data[key_end:value_end]

        try:
            key = key_data.decode("utf-8")
            value = value_data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecordError(
                "Record contains invalid UTF-8 data"
            ) from exc

        return cls(
            key=key,
            value=value,
            record_type=record_type,
        )

    @classmethod
    def delete(cls, key: str) -> Record:
        return cls(
            key=key,
            value="",
            record_type=RecordType.DELETE,
        )