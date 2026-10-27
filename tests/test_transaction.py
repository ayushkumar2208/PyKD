from pathlib import Path

import pytest

from pykd.page_manager import PageManager
from pykd.transaction import (
    Transaction,
    TransactionError,
)
from pykd.wal import WAL


@pytest.fixture
def database(tmp_path: Path):
    manager = PageManager(
        tmp_path / "db.pykd"
    )
    manager.open()

    wal = WAL(
        tmp_path / "db.wal"
    )
    wal.open()

    page = manager.allocate_page()

    yield manager, wal, page.page_id

    wal.close()
    manager.close()


def test_transaction_commit(database):
    manager, wal, page_id = database

    tx = Transaction.begin(
        wal,
        manager,
    )

    page = manager.read_page(page_id)
    after = bytearray(page.data)

    after[16:21] = b"hello"

    tx.update_page(
        page_id,
        bytes(after),
    )

    tx.commit()

    result = manager.read_page(
        page_id
    )

    assert result.read(
        16,
        5,
    ) == b"hello"

    assert not tx.active


def test_transaction_rollback(database):
    manager, wal, page_id = database

    tx = Transaction.begin(
        wal,
        manager,
    )

    page = manager.read_page(page_id)
    after = bytearray(page.data)

    after[16:21] = b"hello"

    tx.update_page(
        page_id,
        bytes(after),
    )

    tx.rollback()

    result = manager.read_page(
        page_id
    )

    assert result.read(
        16,
        5,
    ) == b"\x00" * 5

    assert not tx.active


def test_commit_twice_fails(database):
    manager, wal, page_id = database

    tx = Transaction.begin(
        wal,
        manager,
    )

    tx.commit()

    with pytest.raises(TransactionError):
        tx.commit()


def test_rollback_twice_fails(database):
    manager, wal, page_id = database

    tx = Transaction.begin(
        wal,
        manager,
    )

    tx.rollback()

    with pytest.raises(TransactionError):
        tx.rollback()


def test_update_after_commit_fails(database):
    manager, wal, page_id = database

    tx = Transaction.begin(
        wal,
        manager,
    )

    tx.commit()

    page = manager.read_page(page_id)

    with pytest.raises(TransactionError):
        tx.update_page(
            page_id,
            page.data,
        )