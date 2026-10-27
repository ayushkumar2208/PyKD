from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterator

from .page import PAGE_HEADER_SIZE, PAGE_SIZE, Page
from .page_manager import PageManager
from .record import Record, RecordError, RecordType


RECORD_LENGTH_FORMAT = ">I"
RECORD_LENGTH_SIZE = struct.calcsize(RECORD_LENGTH_FORMAT)


class RecordManagerError(Exception):
    pass


@dataclass(frozen=True)
class RecordLocation:
    page_id: int
    offset: int

    def __post_init__(self) -> None:
        if self.page_id < 0:
            raise ValueError("Page ID cannot be negative")

        if self.offset < PAGE_HEADER_SIZE:
            raise ValueError(
                "Record offset is inside page header"
            )


class RecordManager:
    def __init__(self, page_manager: PageManager):
        self.page_manager = page_manager

    def append(self, record: Record) -> RecordLocation:
        if not isinstance(record, Record):
            raise TypeError("Expected a Record instance")

        payload = record.serialize()

        required_size = (
            RECORD_LENGTH_SIZE + len(payload)
        )

        if required_size > self._max_record_size():
            raise RecordManagerError(
                "Record is too large to fit inside a page"
            )

        page_count = self.page_manager.page_count()

        for page_id in range(page_count):
            page = self.page_manager.read_page(page_id)
            offset = self._find_free_offset(page)

            if self._remaining_space(offset) >= required_size:
                return self._write_record(
                    page,
                    offset,
                    payload,
                )

        page = self.page_manager.allocate_page()

        return self._write_record(
            page,
            PAGE_HEADER_SIZE,
            payload,
        )

    def read(self, location: RecordLocation) -> Record:
        if not isinstance(location, RecordLocation):
            raise TypeError(
                "Expected a RecordLocation"
            )

        page = self.page_manager.read_page(
            location.page_id
        )

        payload = self._read_payload(
            page,
            location.offset,
        )

        try:
            return Record.deserialize(payload)
        except RecordError as exc:
            raise RecordManagerError(
                "Invalid record at requested location"
            ) from exc

    def scan_page(
        self,
        page_id: int,
    ) -> Iterator[tuple[RecordLocation, Record]]:
        page = self.page_manager.read_page(page_id)

        offset = PAGE_HEADER_SIZE

        while offset < PAGE_SIZE:
            remaining = PAGE_SIZE - offset

            if remaining < RECORD_LENGTH_SIZE:
                if self._is_zero_region(page, offset):
                    break

                raise RecordManagerError(
                    f"Corrupted record length at page "
                    f"{page_id}, offset {offset}"
                )

            length_data = page.read(
                offset,
                RECORD_LENGTH_SIZE,
            )

            record_length = struct.unpack(
                RECORD_LENGTH_FORMAT,
                length_data,
            )[0]

            if record_length == 0:
                break

            if record_length > (
                remaining - RECORD_LENGTH_SIZE
            ):
                raise RecordManagerError(
                    f"Record exceeds page boundary at "
                    f"page {page_id}, offset {offset}"
                )

            payload = page.read(
                offset + RECORD_LENGTH_SIZE,
                record_length,
            )

            try:
                record = Record.deserialize(payload)
            except RecordError as exc:
                raise RecordManagerError(
                    f"Invalid record at page {page_id}, "
                    f"offset {offset}"
                ) from exc

            location = RecordLocation(
                page_id=page_id,
                offset=offset,
            )

            yield location, record

            offset += (
                RECORD_LENGTH_SIZE
                + record_length
            )

    def scan(
        self,
    ) -> Iterator[tuple[RecordLocation, Record]]:
        page_count = self.page_manager.page_count()

        for page_id in range(page_count):
            yield from self.scan_page(page_id)

    def find(
        self,
        key: str,
    ) -> RecordLocation | None:
        if not isinstance(key, str):
            raise TypeError(
                "Record key must be a string"
            )

        latest_location = None

        for location, record in self.scan():
            if record.key != key:
                continue

            latest_location = location

            if record.record_type == RecordType.DELETE:
                return None

        return latest_location

    def find_all(
        self,
        key: str,
    ) -> list[RecordLocation]:
        if not isinstance(key, str):
            raise TypeError(
                "Record key must be a string"
            )

        locations = []

        for location, record in self.scan():
            if record.key == key:
                locations.append(location)

        return locations

    def count(self) -> int:
        return sum(
            1
            for _ in self.scan()
        )

    def page_record_count(
        self,
        page_id: int,
    ) -> int:
        return sum(
            1
            for _ in self.scan_page(page_id)
        )

    def _write_record(
        self,
        page: Page,
        offset: int,
        payload: bytes,
    ) -> RecordLocation:
        record_length = len(payload)

        length_data = struct.pack(
            RECORD_LENGTH_FORMAT,
            record_length,
        )

        page.write(
            offset,
            length_data,
        )

        page.write(
            offset + RECORD_LENGTH_SIZE,
            payload,
        )

        self.page_manager.write_page(page)

        return RecordLocation(
            page_id=page.page_id,
            offset=offset,
        )

    def _read_payload(
        self,
        page: Page,
        offset: int,
    ) -> bytes:
        if offset < PAGE_HEADER_SIZE:
            raise RecordManagerError(
                "Record offset is inside page header"
            )

        if offset + RECORD_LENGTH_SIZE > PAGE_SIZE:
            raise RecordManagerError(
                "Record length exceeds page boundary"
            )

        length_data = page.read(
            offset,
            RECORD_LENGTH_SIZE,
        )

        record_length = struct.unpack(
            RECORD_LENGTH_FORMAT,
            length_data,
        )[0]

        if record_length == 0:
            raise RecordManagerError(
                "No record exists at requested location"
            )

        if (
            offset
            + RECORD_LENGTH_SIZE
            + record_length
            > PAGE_SIZE
        ):
            raise RecordManagerError(
                "Record exceeds page boundary"
            )

        return page.read(
            offset + RECORD_LENGTH_SIZE,
            record_length,
        )

    def _find_free_offset(
        self,
        page: Page,
    ) -> int:
        offset = PAGE_HEADER_SIZE

        while offset < PAGE_SIZE:
            remaining = PAGE_SIZE - offset

            if remaining < RECORD_LENGTH_SIZE:
                if self._is_zero_region(
                    page,
                    offset,
                ):
                    return offset

                raise RecordManagerError(
                    f"Corrupted page {page.page_id}"
                )

            length_data = page.read(
                offset,
                RECORD_LENGTH_SIZE,
            )

            record_length = struct.unpack(
                RECORD_LENGTH_FORMAT,
                length_data,
            )[0]

            if record_length == 0:
                return offset

            if record_length > (
                remaining - RECORD_LENGTH_SIZE
            ):
                raise RecordManagerError(
                    f"Corrupted record on page "
                    f"{page.page_id}"
                )

            offset += (
                RECORD_LENGTH_SIZE
                + record_length
            )

        return offset

    @staticmethod
    def _is_zero_region(
        page: Page,
        offset: int,
    ) -> bool:
        return all(
            byte == 0
            for byte in page.read(
                offset,
                PAGE_SIZE - offset,
            )
        )

    @staticmethod
    def _remaining_space(offset: int) -> int:
        return PAGE_SIZE - offset

    @staticmethod
    def _max_record_size() -> int:
        return (
            PAGE_SIZE
            - PAGE_HEADER_SIZE
            - RECORD_LENGTH_SIZE
        )