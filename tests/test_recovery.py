from pathlib import Path

from pykd.page_manager import PageManager
from pykd.recovery import RecoveryManager
from pykd.wal import WAL


def test_recovery_redoes_committed_page(
    tmp_path: Path,
):
    db = tmp_path / "db.pykd"
    wal_path = tmp_path / "db.wal"

    manager = PageManager(db)
    manager.open()

    page = manager.allocate_page()

    before = page.data

    page.write(16, b"hello")
    after = page.data

    page.clear()
    manager.write_page(page)

    wal = WAL(wal_path)
    wal.open()

    wal.begin(1)
    wal.update(
        1,
        page.page_id,
        before,
        after,
    )
    wal.commit(1)

    recovery = RecoveryManager(
        manager,
        wal,
    )

    recovery.recover()

    restored = manager.read_page(
        page.page_id
    )

    assert restored.read(
        16,
        5,
    ) == b"hello"

    wal.close()
    manager.close()


def test_recovery_undoes_uncommitted_page(
    tmp_path: Path,
):
    db = tmp_path / "db.pykd"
    wal_path = tmp_path / "db.wal"

    manager = PageManager(db)
    manager.open()

    page = manager.allocate_page()

    before = page.data

    page.write(16, b"hello")
    after = page.data

    manager.write_page(page)

    wal = WAL(wal_path)
    wal.open()

    wal.begin(1)
    wal.update(
        1,
        page.page_id,
        before,
        after,
    )

    recovery = RecoveryManager(
        manager,
        wal,
    )

    recovery.recover()

    restored = manager.read_page(
        page.page_id
    )

    assert restored.read(
        16,
        5,
    ) == b"\x00" * 5

    wal.close()
    manager.close()