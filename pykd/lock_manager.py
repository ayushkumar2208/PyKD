from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Condition, RLock


class LockError(Exception):
    pass


class LockConflictError(LockError):
    pass


class LockNotHeldError(LockError):
    pass


class LockType(Enum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


@dataclass(frozen=True)
class Lock:
    transaction_id: int
    resource: str
    lock_type: LockType


class LockManager:
    def __init__(self):
        self._condition = Condition(RLock())
        self._locks: dict[str, list[Lock]] = {}
        self._transactions: dict[int, set[str]] = {}

    def acquire_shared(
        self,
        transaction_id: int,
        resource: str,
    ) -> None:
        self._acquire(
            transaction_id,
            resource,
            LockType.SHARED,
        )

    def acquire_exclusive(
        self,
        transaction_id: int,
        resource: str,
    ) -> None:
        self._acquire(
            transaction_id,
            resource,
            LockType.EXCLUSIVE,
        )

    def release(
        self,
        transaction_id: int,
        resource: str,
    ) -> None:
        with self._condition:
            locks = self._locks.get(resource)

            if not locks:
                raise LockNotHeldError(
                    f"No lock exists for {resource}"
                )

            index = next(
                (
                    i
                    for i, lock in enumerate(locks)
                    if lock.transaction_id
                    == transaction_id
                ),
                None,
            )

            if index is None:
                raise LockNotHeldError(
                    f"Transaction {transaction_id} "
                    f"does not hold {resource}"
                )

            locks.pop(index)

            held = self._transactions.get(
                transaction_id
            )

            if held is not None:
                held.discard(resource)

                if not held:
                    self._transactions.pop(
                        transaction_id,
                        None,
                    )

            if not locks:
                self._locks.pop(resource, None)

            self._condition.notify_all()

    def release_all(
        self,
        transaction_id: int,
    ) -> None:
        with self._condition:
            resources = list(
                self._transactions.get(
                    transaction_id,
                    set(),
                )
            )

            for resource in resources:
                locks = self._locks.get(resource)

                if locks is None:
                    continue

                self._locks[resource] = [
                    lock
                    for lock in locks
                    if lock.transaction_id
                    != transaction_id
                ]

                if not self._locks[resource]:
                    self._locks.pop(
                        resource,
                        None,
                    )

            self._transactions.pop(
                transaction_id,
                None,
            )

            self._condition.notify_all()

    def upgrade(
        self,
        transaction_id: int,
        resource: str,
    ) -> None:
        with self._condition:
            locks = self._locks.get(
                resource,
                [],
            )

            own = [
                lock
                for lock in locks
                if lock.transaction_id
                == transaction_id
            ]

            if not own:
                raise LockNotHeldError(
                    f"Transaction {transaction_id} "
                    f"does not hold {resource}"
                )

            if any(
                lock.lock_type
                == LockType.EXCLUSIVE
                for lock in own
            ):
                return

            others = [
                lock
                for lock in locks
                if lock.transaction_id
                != transaction_id
            ]

            if others:
                raise LockConflictError(
                    f"Cannot upgrade {resource}; "
                    "other transactions hold locks"
                )

            self._locks[resource] = [
                lock
                for lock in locks
                if lock.transaction_id
                != transaction_id
            ]

            self._locks[resource].append(
                Lock(
                    transaction_id,
                    resource,
                    LockType.EXCLUSIVE,
                )
            )

            self._condition.notify_all()

    def holds(
        self,
        transaction_id: int,
        resource: str,
    ) -> bool:
        with self._condition:
            return any(
                lock.transaction_id
                == transaction_id
                for lock in self._locks.get(
                    resource,
                    [],
                )
            )

    def lock_type(
        self,
        transaction_id: int,
        resource: str,
    ) -> LockType | None:
        with self._condition:
            for lock in self._locks.get(
                resource,
                [],
            ):
                if (
                    lock.transaction_id
                    == transaction_id
                ):
                    return lock.lock_type

            return None

    def locks_for(
        self,
        transaction_id: int,
    ) -> list[Lock]:
        with self._condition:
            result = []

            for resource in self._transactions.get(
                transaction_id,
                set(),
            ):
                for lock in self._locks.get(
                    resource,
                    [],
                ):
                    if (
                        lock.transaction_id
                        == transaction_id
                    ):
                        result.append(lock)

            return result

    def _acquire(
        self,
        transaction_id: int,
        resource: str,
        lock_type: LockType,
    ) -> None:
        if transaction_id < 0:
            raise ValueError(
                "Transaction ID cannot be negative"
            )

        if not resource:
            raise ValueError(
                "Resource cannot be empty"
            )

        with self._condition:
            existing = self._locks.get(
                resource,
                [],
            )

            own = next(
                (
                    lock
                    for lock in existing
                    if lock.transaction_id
                    == transaction_id
                ),
                None,
            )

            if own is not None:
                if (
                    own.lock_type
                    == LockType.EXCLUSIVE
                ):
                    return

                if lock_type == LockType.SHARED:
                    return

                raise LockConflictError(
                    f"Transaction {transaction_id} "
                    "must upgrade its shared lock"
                )

            if lock_type == LockType.SHARED:
                conflict = any(
                    lock.lock_type
                    == LockType.EXCLUSIVE
                    for lock in existing
                )
            else:
                conflict = bool(existing)

            if conflict:
                raise LockConflictError(
                    f"Resource {resource} "
                    "is currently locked"
                )

            lock = Lock(
                transaction_id,
                resource,
                lock_type,
            )

            self._locks.setdefault(
                resource,
                [],
            ).append(lock)

            self._transactions.setdefault(
                transaction_id,
                set(),
            ).add(resource)