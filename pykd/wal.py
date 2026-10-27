from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


WAL_MAGIC = b"PKWL"
WAL_VERSION = 1

HEADER_FORMAT = ">4sBQQQBI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

TYPE_BEGIN = 1
TYPE_UPDATE = 2
TYPE_COMMIT = 3
TYPE_ABORT = 4
TYPE_CHECKPOINT = 5


class WALError(Exception):
    pass


@dataclass(frozen=True)
class WALRecord:
    lsn: int
    transaction_id: int
    page_id: int
    record_type: int
    before: bytes
    after: bytes


class WAL:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._file = None
        self._next_lsn = 1

    def open(self) -> None:
        if self._file is not None:
            return

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.path.exists():
            self.path.touch()

        self._file = self.path.open("a+b")

        records = self.records()

        if records:
            self._next_lsn = records[-1].lsn + 1

    def close(self) -> None:
        if self._file is None:
            return

        try:
            self.sync()
        finally:
            self._file.close()
            self._file = None

    def begin(self, transaction_id: int) -> int:
        return self._append(
            transaction_id,
            0,
            TYPE_BEGIN,
            b"",
            b"",
        )

    def update(
        self,
        transaction_id: int,
        page_id: int,
        before: bytes,
        after: bytes,
    ) -> int:
        if not isinstance(before, bytes):
            raise TypeError("before must be bytes")

        if not isinstance(after, bytes):
            raise TypeError("after must be bytes")

        return self._append(
            transaction_id,
            page_id,
            TYPE_UPDATE,
            before,
            after,
        )

    def commit(self, transaction_id: int) -> int:
        lsn = self._append(
            transaction_id,
            0,
            TYPE_COMMIT,
            b"",
            b"",
        )

        self.sync()

        return lsn

    def abort(self, transaction_id: int) -> int:
        return self._append(
            transaction_id,
            0,
            TYPE_ABORT,
            b"",
            b"",
        )

    def checkpoint(self) -> int:
        return self._append(
            0,
            0,
            TYPE_CHECKPOINT,
            b"",
            b"",
        )

    def records(self) -> list[WALRecord]:
        self._ensure_open()

        self._file.flush()
        self._file.seek(0)

        result = []

        while True:
            header = self._file.read(
                HEADER_SIZE
            )

            if not header:
                break

            if len(header) != HEADER_SIZE:
                raise WALError(
                    "Truncated WAL header"
                )

            (
                magic,
                version,
                lsn,
                transaction_id,
                page_id,
                record_type,
                payload_size,
            ) = struct.unpack(
                HEADER_FORMAT,
                header,
            )

            if magic != WAL_MAGIC:
                raise WALError(
                    "Invalid WAL magic"
                )

            if version != WAL_VERSION:
                raise WALError(
                    "Unsupported WAL version"
                )

            payload = self._file.read(
                payload_size
            )

            if len(payload) != payload_size:
                raise WALError(
                    "Truncated WAL payload"
                )

            if payload_size:
                before_size = struct.unpack(
                    ">I",
                    payload[:4],
                )[0]

                before_start = 4
                before_end = (
                    before_start + before_size
                )

                before = payload[
                    before_start:before_end
                ]

                after_size = struct.unpack(
                    ">I",
                    payload[before_end:before_end + 4],
                )[0]

                after_start = before_end + 4
                after_end = (
                    after_start + after_size
                )

                after = payload[
                    after_start:after_end
                ]
            else:
                before = b""
                after = b""

            result.append(
                WALRecord(
                    lsn=lsn,
                    transaction_id=transaction_id,
                    page_id=page_id,
                    record_type=record_type,
                    before=before,
                    after=after,
                )
            )

        self._file.seek(0, 2)

        return result

    def sync(self) -> None:
        self._ensure_open()
        self._file.flush()

    def _append(
        self,
        transaction_id: int,
        page_id: int,
        record_type: int,
        before: bytes,
        after: bytes,
    ) -> int:
        self._ensure_open()

        payload = (
            struct.pack(">I", len(before))
            + before
            + struct.pack(">I", len(after))
            + after
        )

        lsn = self._next_lsn
        self._next_lsn += 1

        header = struct.pack(
            HEADER_FORMAT,
            WAL_MAGIC,
            WAL_VERSION,
            lsn,
            transaction_id,
            page_id,
            record_type,
            len(payload),
        )

        self._file.seek(0, 2)
        self._file.write(header)
        self._file.write(payload)

        return lsn

    def _ensure_open(self) -> None:
        if self._file is None:
            raise WALError(
                "WAL is not open"
            )