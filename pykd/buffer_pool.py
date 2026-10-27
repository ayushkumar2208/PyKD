from __future__ import annotations

from collections import OrderedDict

from .page import Page
from .page_manager import PageManager


class BufferPoolError(Exception):
    pass


class BufferPoolFullError(BufferPoolError):
    pass


class PagePinnedError(BufferPoolError):
    pass


class PageNotFoundError(BufferPoolError):
    pass


class BufferPool:
    def __init__(
        self,
        page_manager: PageManager,
        capacity: int = 16,
    ):
        if capacity <= 0:
            raise ValueError(
                "Buffer pool capacity must be positive"
            )

        self.page_manager = page_manager
        self.capacity = capacity

        self._pages: dict[int, Page] = {}
        self._dirty: set[int] = set()
        self._pin_count: dict[int, int] = {}

        self._lru: OrderedDict[int, None] = (
            OrderedDict()
        )

    def fetch_page(self, page_id: int) -> Page:
        self._validate_page_id(page_id)

        if page_id in self._pages:
            self._touch(page_id)
            return self._pages[page_id]

        if len(self._pages) >= self.capacity:
            self._evict()

        try:
            page = self.page_manager.read_page(page_id)
        except Exception as exc:
            raise PageNotFoundError(
                f"Page {page_id} could not be loaded"
            ) from exc

        self._pages[page_id] = page
        self._pin_count.setdefault(page_id, 0)
        self._touch(page_id)

        return page

    def new_page(self) -> Page:
        if len(self._pages) >= self.capacity:
            self._evict()

        page = self.page_manager.allocate_page()

        self._pages[page.page_id] = page
        self._pin_count[page.page_id] = 0
        self._touch(page.page_id)

        return page

    def pin_page(self, page_id: int) -> None:
        self._validate_page_id(page_id)

        if page_id not in self._pages:
            self.fetch_page(page_id)

        self._pin_count[page_id] += 1
        self._touch(page_id)

    def unpin_page(
        self,
        page_id: int,
        dirty: bool = False,
    ) -> None:
        self._validate_page_id(page_id)

        if page_id not in self._pages:
            raise PageNotFoundError(
                f"Page {page_id} is not in buffer pool"
            )

        if self._pin_count[page_id] <= 0:
            raise BufferPoolError(
                f"Page {page_id} is not pinned"
            )

        self._pin_count[page_id] -= 1

        if dirty:
            self._dirty.add(page_id)

        self._touch(page_id)

    def mark_dirty(self, page_id: int) -> None:
        self._validate_page_id(page_id)

        if page_id not in self._pages:
            raise PageNotFoundError(
                f"Page {page_id} is not in buffer pool"
            )

        self._dirty.add(page_id)

    def flush_page(self, page_id: int) -> None:
        self._validate_page_id(page_id)

        if page_id not in self._pages:
            raise PageNotFoundError(
                f"Page {page_id} is not in buffer pool"
            )

        page = self._pages[page_id]

        self.page_manager.write_page(page)

        self._dirty.discard(page_id)

        self._touch(page_id)

    def flush_all(self) -> None:
        for page_id in list(self._pages):
            if page_id in self._dirty:
                self.flush_page(page_id)

        self.page_manager.sync()

    def evict_page(self, page_id: int) -> bool:
        self._validate_page_id(page_id)

        if page_id not in self._pages:
            return False

        if self._pin_count.get(page_id, 0) > 0:
            raise PagePinnedError(
                f"Page {page_id} is pinned"
            )

        if page_id in self._dirty:
            self.flush_page(page_id)

        del self._pages[page_id]
        self._dirty.discard(page_id)
        self._pin_count.pop(page_id, None)
        self._lru.pop(page_id, None)

        return True

    def contains(self, page_id: int) -> bool:
        return page_id in self._pages

    def is_dirty(self, page_id: int) -> bool:
        return page_id in self._dirty

    def is_pinned(self, page_id: int) -> bool:
        return self._pin_count.get(page_id, 0) > 0

    def pin_count(self, page_id: int) -> int:
        return self._pin_count.get(page_id, 0)

    def size(self) -> int:
        return len(self._pages)

    def available(self) -> int:
        return self.capacity - len(self._pages)

    def clear(self) -> None:
        for page_id in list(self._pages):
            if self._pin_count.get(page_id, 0) > 0:
                raise PagePinnedError(
                    f"Page {page_id} is pinned"
                )

        self.flush_all()

        self._pages.clear()
        self._dirty.clear()
        self._pin_count.clear()
        self._lru.clear()

    def _evict(self) -> None:
        for page_id in list(self._lru):
            if self._pin_count.get(page_id, 0) > 0:
                continue

            self.evict_page(page_id)
            return

        raise BufferPoolFullError(
            "No unpinned page available for eviction"
        )

    def _touch(self, page_id: int) -> None:
        self._lru.pop(page_id, None)
        self._lru[page_id] = None

    @staticmethod
    def _validate_page_id(page_id: int) -> None:
        if not isinstance(page_id, int):
            raise TypeError(
                "Page ID must be an integer"
            )

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative"
            )