from __future__ import annotations

from collections.abc import Iterator

from .record_manager import RecordLocation


class IndexError(Exception):
    pass


class Index:
    def __init__(self) -> None:
        self._entries: dict[str, RecordLocation] = {}

    def set(
        self,
        key: str,
        location: RecordLocation,
    ) -> None:
        self._validate_key(key)

        if not isinstance(location, RecordLocation):
            raise TypeError(
                "Location must be a RecordLocation"
            )

        self._entries[key] = location

    def get(
        self,
        key: str,
    ) -> RecordLocation | None:
        self._validate_key(key)

        return self._entries.get(key)

    def delete(self, key: str) -> bool:
        self._validate_key(key)

        if key not in self._entries:
            return False

        del self._entries[key]

        return True

    def exists(self, key: str) -> bool:
        self._validate_key(key)

        return key in self._entries

    def keys(self) -> list[str]:
        return list(self._entries.keys())

    def values(self) -> list[RecordLocation]:
        return list(self._entries.values())

    def items(
        self,
    ) -> list[tuple[str, RecordLocation]]:
        return list(self._entries.items())

    def clear(self) -> None:
        self._entries.clear()

    def count(self) -> int:
        return len(self._entries)

    def is_empty(self) -> bool:
        return not self._entries

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def __len__(self) -> int:
        return self.count()

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError(
                "Index key must be a string"
            )

        if not key:
            raise ValueError(
                "Index key cannot be empty"
            )

        if "\x00" in key:
            raise ValueError(
                "Index key contains a null character"
            )