from __future__ import annotations

from pathlib import Path
from typing import Optional

from .storage import StorageEngine


class Database:
    """
    Core PyKD database interface.

    Responsible for:
    - database initialization
    - key/value operations
    - persistence through StorageEngine
    - database lifecycle management
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.storage = StorageEngine(self.path)
        self._opened = False

    def open(self) -> None:
        if self._opened:
            return

        self.storage.open()
        self._opened = True

    def close(self) -> None:
        if not self._opened:
            return

        self.storage.close()
        self._opened = False

    def set(self, key: str, value: str) -> None:
        self._ensure_open()

        self._validate_key(key)
        self.storage.put(key, value)

    def get(self, key: str) -> Optional[str]:
        self._ensure_open()

        self._validate_key(key)
        return self.storage.get(key)

    def delete(self, key: str) -> bool:
        self._ensure_open()

        self._validate_key(key)
        return self.storage.delete(key)

    def exists(self, key: str) -> bool:
        self._ensure_open()

        self._validate_key(key)
        return self.storage.exists(key)

    def keys(self) -> list[str]:
        self._ensure_open()
        return self.storage.keys()

    def clear(self) -> None:
        self._ensure_open()
        self.storage.clear()

    def sync(self) -> None:
        self._ensure_open()
        self.storage.sync()

    def _ensure_open(self) -> None:
        if not self._opened:
            raise RuntimeError("Database is not open")

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("Database key must be a string")

        if not key:
            raise ValueError("Database key cannot be empty")

        if "\x00" in key:
            raise ValueError("Database key contains an invalid null character")

    def __enter__(self) -> Database:
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()