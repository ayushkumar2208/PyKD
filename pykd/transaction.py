from __future__ import annotations

from dataclasses import dataclass
from itertools import count

from .page_manager import PageManager
from .wal import WAL


class TransactionError(Exception):
    pass


_tx_ids = count(1)


@dataclass
class Transaction:
    transaction_id: int
    wal: WAL
    page_manager: PageManager
    active: bool = True

    @classmethod
    def begin(
        cls,
        wal: WAL,
        page_manager: PageManager,
    ) -> Transaction:
        transaction_id = next(_tx_ids)

        wal.begin(transaction_id)

        return cls(
            transaction_id=transaction_id,
            wal=wal,
            page_manager=page_manager,
        )

    def update_page(
        self,
        page_id: int,
        after: bytes,
    ) -> None:
        self._ensure_active()

        page = self.page_manager.read_page(
            page_id
        )

        before = page.data

        if len(after) != len(before):
            raise TransactionError(
                "Page image size mismatch"
            )

        self.wal.update(
            self.transaction_id,
            page_id,
            before,
            after,
        )

        page.clear()

        page.write(
            8,
            after[8:],
        )

        self.page_manager.write_page(
            page
        )

    def commit(self) -> None:
        self._ensure_active()

        self.wal.commit(
            self.transaction_id
        )

        self.page_manager.sync()

        self.active = False

    def rollback(self) -> None:
        self._ensure_active()

        records = self.wal.records()

        for record in reversed(records):
            if (
                record.transaction_id
                != self.transaction_id
            ):
                continue

            if not record.before:
                continue

            page = self.page_manager.read_page(
                record.page_id
            )

            page.clear()

            page.write(
                8,
                record.before[8:],
            )

            self.page_manager.write_page(
                page
            )

        self.wal.abort(
            self.transaction_id
        )

        self.page_manager.sync()

        self.active = False

    def _ensure_active(self) -> None:
        if not self.active:
            raise TransactionError(
                "Transaction is no longer active"
            )