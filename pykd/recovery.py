from __future__ import annotations

from .page_manager import PageManager
from .wal import (
    TYPE_ABORT,
    TYPE_BEGIN,
    TYPE_COMMIT,
    TYPE_UPDATE,
    WAL,
)


class RecoveryError(Exception):
    pass


class RecoveryManager:
    def __init__(
        self,
        page_manager: PageManager,
        wal: WAL,
    ):
        self.page_manager = page_manager
        self.wal = wal

    def recover(self) -> None:
        records = self.wal.records()

        committed = {
            record.transaction_id
            for record in records
            if record.record_type == TYPE_COMMIT
        }

        active = {
            record.transaction_id
            for record in records
            if record.record_type == TYPE_BEGIN
        }

        for record in records:
            if record.record_type in {
                TYPE_COMMIT,
                TYPE_ABORT,
            }:
                active.discard(
                    record.transaction_id
                )

        self._redo(
            records,
            committed,
        )

        self._undo(
            records,
            active,
        )

        self.page_manager.sync()

    def _redo(
        self,
        records,
        committed,
    ) -> None:
        for record in records:
            if record.record_type != TYPE_UPDATE:
                continue

            if record.transaction_id not in committed:
                continue

            page = self.page_manager.read_page(
                record.page_id
            )

            if len(record.after) != len(page.data):
                raise RecoveryError(
                    "WAL page image size mismatch"
                )

            page.clear()

            page.write(
                8,
                record.after[8:],
            )

            self.page_manager.write_page(
                page
            )

    def _undo(
        self,
        records,
        active,
    ) -> None:
        for record in reversed(records):
            if record.record_type != TYPE_UPDATE:
                continue

            if record.transaction_id not in active:
                continue

            page = self.page_manager.read_page(
                record.page_id
            )

            if len(record.before) != len(page.data):
                raise RecoveryError(
                    "WAL page image size mismatch"
                )

            page.clear()

            page.write(
                8,
                record.before[8:],
            )

            self.page_manager.write_page(
                page
            )