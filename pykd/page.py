from __future__ import annotations

import struct
from dataclasses import dataclass


PAGE_SIZE = 4096

PAGE_HEADER_FORMAT = ">II"
PAGE_HEADER_SIZE = struct.calcsize(PAGE_HEADER_FORMAT)

PAGE_TYPE_DATA = 1


class PageError(Exception):
    pass


@dataclass
class Page:
    page_id: int
    page_type: int = PAGE_TYPE_DATA

    def __post_init__(self) -> None:
        if self.page_id < 0:
            raise ValueError("Page ID cannot be negative")

        if self.page_type < 0:
            raise ValueError("Page type cannot be negative")

        self._data = bytearray(PAGE_SIZE)

    @property
    def data(self) -> bytes:
        return bytes(self._data)

    @property
    def usable_size(self) -> int:
        return PAGE_SIZE - PAGE_HEADER_SIZE

    def write(self, offset: int, data: bytes) -> None:
        if offset < PAGE_HEADER_SIZE:
            raise PageError(
                f"Data cannot be written before offset {PAGE_HEADER_SIZE}"
            )

        if offset + len(data) > PAGE_SIZE:
            raise PageError("Data exceeds page boundary")

        self._data[offset:offset + len(data)] = data

    def read(self, offset: int, length: int) -> bytes:
        if offset < PAGE_HEADER_SIZE:
            raise PageError(
                f"Data cannot be read before offset {PAGE_HEADER_SIZE}"
            )

        if length < 0:
            raise ValueError("Length cannot be negative")

        if offset + length > PAGE_SIZE:
            raise PageError("Read exceeds page boundary")

        return bytes(self._data[offset:offset + length])

    def clear(self) -> None:
        self._data = bytearray(PAGE_SIZE)

    def serialize(self) -> bytes:
        header = struct.pack(
            PAGE_HEADER_FORMAT,
            self.page_id,
            self.page_type,
        )

        self._data[:PAGE_HEADER_SIZE] = header

        return bytes(self._data)

    @classmethod
    def deserialize(cls, raw: bytes) -> Page:
        if len(raw) != PAGE_SIZE:
            raise PageError(
                f"Invalid page size: expected {PAGE_SIZE}, "
                f"got {len(raw)}"
            )

        page_id, page_type = struct.unpack(
            PAGE_HEADER_FORMAT,
            raw[:PAGE_HEADER_SIZE],
        )

        page = cls(
            page_id=page_id,
            page_type=page_type,
        )

        page._data[:] = raw

        return page

    def is_empty(self) -> bool:
        return all(
            byte == 0
            for byte in self._data[PAGE_HEADER_SIZE:]
        )