from __future__ import annotations

import os
from pathlib import Path

from .page import PAGE_SIZE, Page, PageError


class PageManagerError(Exception):
    pass


class PageManager:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._file = None

    def open(self) -> None:
        if self._file is not None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.touch()

        self._file = self.path.open("r+b")

    def close(self) -> None:
        if self._file is None:
            return

        try:
            self.sync()
        finally:
            self._file.close()
            self._file = None

    def page_count(self) -> int:
        self._ensure_open()

        size = self._file.seek(0, os.SEEK_END)

        if size % PAGE_SIZE != 0:
            raise PageManagerError(
                "Database file is not aligned to page size"
            )

        return size // PAGE_SIZE

    def read_page(self, page_id: int) -> Page:
        self._ensure_open()
        self._validate_page_id(page_id)

        offset = page_id * PAGE_SIZE

        self._file.seek(0, os.SEEK_END)
        file_size = self._file.tell()

        if offset + PAGE_SIZE > file_size:
            raise PageManagerError(
                f"Page {page_id} does not exist"
            )

        self._file.seek(offset)

        raw = self._file.read(PAGE_SIZE)

        if len(raw) != PAGE_SIZE:
            raise PageManagerError(
                f"Could not read complete page {page_id}"
            )

        try:
            return Page.deserialize(raw)
        except PageError as exc:
            raise PageManagerError(
                f"Invalid page {page_id}"
            ) from exc

    def write_page(self, page: Page) -> None:
        self._ensure_open()

        if not isinstance(page, Page):
            raise TypeError("Expected a Page instance")

        raw = page.serialize()

        if len(raw) != PAGE_SIZE:
            raise PageManagerError(
                "Serialized page has invalid size"
            )

        offset = page.page_id * PAGE_SIZE

        self._file.seek(offset)
        self._file.write(raw)
        self._file.flush()

    def allocate_page(self) -> Page:
        self._ensure_open()

        page_id = self.page_count()

        page = Page(page_id=page_id)

        self.write_page(page)

        return page

    def sync(self) -> None:
        self._ensure_open()

        self._file.flush()
        os.fsync(self._file.fileno())

    def _ensure_open(self) -> None:
        if self._file is None:
            raise PageManagerError(
                "Page manager is not open"
            )

    @staticmethod
    def _validate_page_id(page_id: int) -> None:
        if not isinstance(page_id, int):
            raise TypeError("Page ID must be an integer")

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative"
            )