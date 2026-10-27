import pytest

from pykd.lock_manager import (
    LockConflictError,
    LockManager,
    LockNotHeldError,
    LockType,
)


def test_shared_locks_can_coexist():
    manager = LockManager()

    manager.acquire_shared(1, "users")
    manager.acquire_shared(2, "users")

    assert manager.lock_type(
        1,
        "users",
    ) == LockType.SHARED

    assert manager.lock_type(
        2,
        "users",
    ) == LockType.SHARED


def test_exclusive_blocks_shared():
    manager = LockManager()

    manager.acquire_exclusive(1, "users")

    with pytest.raises(LockConflictError):
        manager.acquire_shared(
            2,
            "users",
        )


def test_exclusive_blocks_exclusive():
    manager = LockManager()

    manager.acquire_exclusive(1, "users")

    with pytest.raises(LockConflictError):
        manager.acquire_exclusive(
            2,
            "users",
        )


def test_shared_blocks_exclusive():
    manager = LockManager()

    manager.acquire_shared(1, "users")

    with pytest.raises(LockConflictError):
        manager.acquire_exclusive(
            2,
            "users",
        )


def test_same_shared_lock_is_idempotent():
    manager = LockManager()

    manager.acquire_shared(1, "users")
    manager.acquire_shared(1, "users")

    assert len(
        manager.locks_for(1)
    ) == 1


def test_same_exclusive_lock_is_idempotent():
    manager = LockManager()

    manager.acquire_exclusive(1, "users")
    manager.acquire_exclusive(1, "users")

    assert len(
        manager.locks_for(1)
    ) == 1


def test_upgrade_shared_to_exclusive():
    manager = LockManager()

    manager.acquire_shared(1, "users")
    manager.upgrade(1, "users")

    assert manager.lock_type(
        1,
        "users",
    ) == LockType.EXCLUSIVE


def test_upgrade_fails_with_other_holder():
    manager = LockManager()

    manager.acquire_shared(1, "users")
    manager.acquire_shared(2, "users")

    with pytest.raises(LockConflictError):
        manager.upgrade(1, "users")


def test_release_lock():
    manager = LockManager()

    manager.acquire_exclusive(1, "users")
    manager.release(1, "users")

    assert not manager.holds(
        1,
        "users",
    )


def test_release_all():
    manager = LockManager()

    manager.acquire_shared(1, "users")
    manager.acquire_exclusive(1, "orders")

    manager.release_all(1)

    assert manager.locks_for(1) == []


def test_resource_available_after_release():
    manager = LockManager()

    manager.acquire_exclusive(1, "users")
    manager.release(1, "users")

    manager.acquire_exclusive(2, "users")

    assert manager.holds(
        2,
        "users",
    )


def test_release_missing_lock():
    manager = LockManager()

    with pytest.raises(LockNotHeldError):
        manager.release(
            1,
            "users",
        )


def test_upgrade_requires_existing_lock():
    manager = LockManager()

    with pytest.raises(LockNotHeldError):
        manager.upgrade(
            1,
            "users",
        )


def test_invalid_transaction_id():
    manager = LockManager()

    with pytest.raises(ValueError):
        manager.acquire_shared(
            -1,
            "users",
        )


def test_empty_resource():
    manager = LockManager()

    with pytest.raises(ValueError):
        manager.acquire_shared(
            1,
            "",
        )