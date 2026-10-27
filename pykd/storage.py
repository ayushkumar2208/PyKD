from __future__ import annotations

from pathlib import Path
from typing import Optional

from .index import Index
from .page_manager import PageManager
from .record import Record, RecordType
from .record_manager import RecordManager


class StorageError(Exception):
    pass


class StorageEngine:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.page_manager = PageManager(self.path)
        self.record_manager = RecordManager(self.page_manager)
        self.index = Index()
        self._opened = False

    def open(self) -> None:
        if self._opened:
            return

        self.page_manager.open()

        try:
            self._rebuild_index()
            self._opened = True
        except Exception:
            self.page_manager.close()
            raise

    def close(self) -> None:
        if not self._opened:
            return

        try:
            self.sync()
        finally:
            self.page_manager.close()
            self._opened = False

    def put(self, key: str, value: str) -> None:
        self._ensure_open()
        self._validate_key(key)

        if not isinstance(value, str):
            raise TypeError("Value must be a string")

        location = self.record_manager.append(
            Record(key, value, RecordType.SET)
        )

        self.index.set(key, location)

    def get(self, key: str) -> Optional[str]:
        self._ensure_open()
        self._validate_key(key)

        location = self.index.get(key)

        if location is None:
            return None

        record = self.record_manager.read(location)

        if record.record_type != RecordType.SET:
            return None

        return record.value

    def delete(self, key: str) -> bool:
        self._ensure_open()
        self._validate_key(key)

        if self.index.get(key) is None:
            return False

        self.record_manager.append(
            Record.delete(key)
        )

        self.index.delete(key)

        return True

    def exists(self, key: str) -> bool:
        self._ensure_open()
        self._validate_key(key)

        return self.index.exists(key)

    def keys(self) -> list[str]:
        self._ensure_open()
        return self.index.keys()

    def clear(self) -> None:
        self._ensure_open()

        for key in self.index.keys():
            self.record_manager.append(
                Record.delete(key)
            )

        self.index.clear()

    def sync(self) -> None:
        self._ensure_open()
        self.page_manager.sync()

    def page_count(self) -> int:
        self._ensure_open()
        return self.page_manager.page_count()

    def record_count(self) -> int:
        self._ensure_open()
        return self.record_manager.count()

    def index_count(self) -> int:
        self._ensure_open()
        return self.index.count()

    def _rebuild_index(self) -> None:
        self.index.clear()

        for location, record in self.record_manager.scan():
            if record.record_type == RecordType.SET:
                self.index.set(record.key, location)

            elif record.record_type == RecordType.DELETE:
                self.index.delete(record.key)

            else:
                raise StorageError(
                    f"Unknown record type: {record.record_type}"
                )

    def _ensure_open(self) -> None:
        if not self._opened:
            raise StorageError(
                "Storage engine is not open"
            )

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("Key must be a string")

        if not key:
            raise ValueError("Key cannot be empty")

        if "\x00" in key:
            raise ValueError(
                "Key contains a null character"
            )