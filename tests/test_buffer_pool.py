from pathlib import Path

import pytest

from pykd.buffer_pool import (
    BufferPool,
    BufferPoolFullError,
    PagePinnedError,
    PageNotFoundError,
)
from pykd.page_manager import PageManager


@pytest.fixture
def manager(tmp_path: Path):
    manager = PageManager(
        tmp_path / "buffer_pool.pykd"
    )
    manager.open()

    yield manager

    manager.close()


def test_empty_pool(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    assert pool.size() == 0
    assert pool.available() == 2


def test_fetch_page(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    fetched = pool.fetch_page(
        page.page_id
    )

    assert fetched.page_id == page.page_id
    assert pool.contains(page.page_id)


def test_fetch_same_page_returns_cached_page(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    first = pool.fetch_page(
        page.page_id
    )

    second = pool.fetch_page(
        page.page_id
    )

    assert first is second
    assert pool.size() == 1


def test_new_page(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    page = pool.new_page()

    assert page.page_id == 0
    assert pool.contains(0)
    assert pool.size() == 1


def test_pin_and_unpin(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)

    pool.pin_page(page.page_id)

    assert pool.is_pinned(page.page_id)
    assert pool.pin_count(page.page_id) == 1

    pool.unpin_page(page.page_id)

    assert not pool.is_pinned(page.page_id)
    assert pool.pin_count(page.page_id) == 0


def test_multiple_pins(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)

    pool.pin_page(page.page_id)
    pool.pin_page(page.page_id)

    assert pool.pin_count(page.page_id) == 2

    pool.unpin_page(page.page_id)
    assert pool.pin_count(page.page_id) == 1

    pool.unpin_page(page.page_id)
    assert pool.pin_count(page.page_id) == 0


def test_unpin_marks_dirty(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)
    pool.pin_page(page.page_id)

    pool.unpin_page(
        page.page_id,
        dirty=True,
    )

    assert pool.is_dirty(page.page_id)


def test_mark_dirty(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)

    pool.mark_dirty(page.page_id)

    assert pool.is_dirty(page.page_id)


def test_flush_page(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    fetched = pool.fetch_page(
        page.page_id
    )

    fetched.write(
        16,
        b"hello",
    )

    pool.mark_dirty(page.page_id)
    pool.flush_page(page.page_id)

    assert not pool.is_dirty(
        page.page_id
    )

    stored = manager.read_page(
        page.page_id
    )

    assert stored.read(
        16,
        5,
    ) == b"hello"


def test_lru_eviction(manager):
    first = manager.allocate_page()
    second = manager.allocate_page()
    third = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(first.page_id)
    pool.fetch_page(second.page_id)

    pool.fetch_page(third.page_id)

    assert not pool.contains(
        first.page_id
    )

    assert pool.contains(
        second.page_id
    )

    assert pool.contains(
        third.page_id
    )


def test_recently_used_page_is_not_evicted(manager):
    first = manager.allocate_page()
    second = manager.allocate_page()
    third = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(first.page_id)
    pool.fetch_page(second.page_id)

    pool.fetch_page(first.page_id)

    pool.fetch_page(third.page_id)

    assert pool.contains(
        first.page_id
    )

    assert not pool.contains(
        second.page_id
    )

    assert pool.contains(
        third.page_id
    )


def test_pinned_page_cannot_be_evicted(manager):
    first = manager.allocate_page()
    second = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=1,
    )

    pool.fetch_page(first.page_id)
    pool.pin_page(first.page_id)

    with pytest.raises(BufferPoolFullError):
        pool.fetch_page(second.page_id)


def test_evict_pinned_page_fails(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)
    pool.pin_page(page.page_id)

    with pytest.raises(PagePinnedError):
        pool.evict_page(page.page_id)


def test_evict_page(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)

    assert pool.evict_page(page.page_id)
    assert not pool.contains(page.page_id)


def test_evict_missing_page(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    assert not pool.evict_page(10)


def test_missing_page(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    with pytest.raises(PageNotFoundError):
        pool.fetch_page(99)


def test_unpin_missing_page(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    with pytest.raises(PageNotFoundError):
        pool.unpin_page(99)


def test_unpin_unpinned_page(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)

    with pytest.raises(
        Exception
    ):
        pool.unpin_page(page.page_id)


def test_dirty_page_survives_eviction(manager):
    first = manager.allocate_page()
    second = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=1,
    )

    page = pool.fetch_page(
        first.page_id
    )

    page.write(
        16,
        b"data",
    )

    pool.mark_dirty(
        first.page_id
    )

    pool.fetch_page(
        second.page_id
    )

    stored = manager.read_page(
        first.page_id
    )

    assert stored.read(
        16,
        4,
    ) == b"data"


def test_flush_all(manager):
    first = manager.allocate_page()
    second = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    page1 = pool.fetch_page(
        first.page_id
    )

    page2 = pool.fetch_page(
        second.page_id
    )

    page1.write(
        16,
        b"one",
    )

    page2.write(
        16,
        b"two",
    )

    pool.mark_dirty(first.page_id)
    pool.mark_dirty(second.page_id)

    pool.flush_all()

    assert not pool.is_dirty(
        first.page_id
    )

    assert not pool.is_dirty(
        second.page_id
    )

    assert manager.read_page(
        first.page_id
    ).read(16, 3) == b"one"

    assert manager.read_page(
        second.page_id
    ).read(16, 3) == b"two"


def test_clear(manager):
    first = manager.allocate_page()
    second = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(first.page_id)
    pool.fetch_page(second.page_id)

    pool.clear()

    assert pool.size() == 0
    assert pool.available() == 2


def test_clear_fails_with_pinned_page(manager):
    page = manager.allocate_page()

    pool = BufferPool(
        manager,
        capacity=2,
    )

    pool.fetch_page(page.page_id)
    pool.pin_page(page.page_id)

    with pytest.raises(PagePinnedError):
        pool.clear()


def test_invalid_capacity(manager):
    with pytest.raises(ValueError):
        BufferPool(
            manager,
            capacity=0,
        )


def test_invalid_page_id(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    with pytest.raises(ValueError):
        pool.fetch_page(-1)


def test_invalid_page_id_type(manager):
    pool = BufferPool(
        manager,
        capacity=2,
    )

    with pytest.raises(TypeError):
        pool.fetch_page("1")