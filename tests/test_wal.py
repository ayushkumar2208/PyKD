from pathlib import Path

from pykd.wal import (
    TYPE_BEGIN,
    TYPE_COMMIT,
    TYPE_UPDATE,
    WAL,
)


def test_wal_begin(tmp_path: Path):
    wal = WAL(tmp_path / "db.wal")
    wal.open()

    lsn = wal.begin(1)

    assert lsn == 1

    records = wal.records()

    assert len(records) == 1
    assert records[0].record_type == TYPE_BEGIN
    assert records[0].transaction_id == 1

    wal.close()


def test_wal_update(tmp_path: Path):
    wal = WAL(tmp_path / "db.wal")
    wal.open()

    wal.begin(1)

    lsn = wal.update(
        1,
        5,
        b"before",
        b"after",
    )

    assert lsn == 2

    records = wal.records()

    assert records[1].record_type == TYPE_UPDATE
    assert records[1].page_id == 5
    assert records[1].before == b"before"
    assert records[1].after == b"after"

    wal.close()


def test_wal_commit(tmp_path: Path):
    wal = WAL(tmp_path / "db.wal")
    wal.open()

    wal.begin(1)
    wal.update(
        1,
        1,
        b"a",
        b"b",
    )

    wal.commit(1)

    records = wal.records()

    assert records[-1].record_type == TYPE_COMMIT

    wal.close()


def test_wal_persistence(tmp_path: Path):
    path = tmp_path / "db.wal"

    wal = WAL(path)
    wal.open()

    wal.begin(1)
    wal.commit(1)

    wal.close()

    reopened = WAL(path)
    reopened.open()

    records = reopened.records()

    assert len(records) == 2
    assert records[0].record_type == TYPE_BEGIN
    assert records[1].record_type == TYPE_COMMIT

    reopened.close()


def test_lsn_increases(tmp_path: Path):
    wal = WAL(tmp_path / "db.wal")
    wal.open()

    first = wal.begin(1)
    second = wal.commit(1)

    assert second > first

    wal.close()