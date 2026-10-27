from pathlib import Path

import pytest

from pykd.page import PAGE_HEADER_SIZE, PAGE_SIZE, Page
from pykd.page_manager import PageManager, PageManagerError


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test.pykd"


@pytest.fixture
def manager(database_path: Path):
    page_manager = PageManager(database_path)
    page_manager.open()

    yield page_manager

    page_manager.close()


def test_database_file_is_created(database_path: Path):
    manager = PageManager(database_path)

    manager.open()

    assert database_path.exists()

    manager.close()


def test_new_database_has_zero_pages(manager: PageManager):
    assert manager.page_count() == 0


def test_allocate_page(manager: PageManager):
    page = manager.allocate_page()

    assert isinstance(page, Page)
    assert page.page_id == 0
    assert manager.page_count() == 1


def test_allocate_multiple_pages(manager: PageManager):
    page1 = manager.allocate_page()
    page2 = manager.allocate_page()
    page3 = manager.allocate_page()

    assert page1.page_id == 0
    assert page2.page_id == 1
    assert page3.page_id == 2
    assert manager.page_count() == 3


def test_write_and_read_page(manager: PageManager):
    page = manager.allocate_page()

    data = b"PyKD page manager"

    page.write(PAGE_HEADER_SIZE, data)
    manager.write_page(page)

    loaded = manager.read_page(page.page_id)

    assert loaded.page_id == page.page_id
    assert loaded.read(
        PAGE_HEADER_SIZE,
        len(data),
    ) == data


def test_page_data_persists_after_reopen(database_path: Path):
    manager = PageManager(database_path)
    manager.open()

    page = manager.allocate_page()

    data = b"persistent page data"

    page.write(PAGE_HEADER_SIZE, data)
    manager.write_page(page)
    manager.close()

    manager = PageManager(database_path)
    manager.open()

    loaded = manager.read_page(0)

    assert loaded.page_id == 0
    assert loaded.read(
        PAGE_HEADER_SIZE,
        len(data),
    ) == data

    manager.close()


def test_pages_are_fixed_size(database_path: Path):
    manager = PageManager(database_path)
    manager.open()

    manager.allocate_page()
    manager.allocate_page()

    manager.close()

    assert database_path.stat().st_size == PAGE_SIZE * 2


def test_read_nonexistent_page(manager: PageManager):
    with pytest.raises(PageManagerError):
        manager.read_page(0)


def test_read_page_beyond_end(manager: PageManager):
    manager.allocate_page()

    with pytest.raises(PageManagerError):
        manager.read_page(1)


def test_negative_page_id_is_rejected(manager: PageManager):
    with pytest.raises(ValueError):
        manager.read_page(-1)


def test_non_integer_page_id_is_rejected(manager: PageManager):
    with pytest.raises(TypeError):
        manager.read_page("0")


def test_write_page_requires_page_object(manager: PageManager):
    with pytest.raises(TypeError):
        manager.write_page("invalid")


def test_page_count_after_reopen(database_path: Path):
    manager = PageManager(database_path)
    manager.open()

    manager.allocate_page()
    manager.allocate_page()
    manager.allocate_page()

    assert manager.page_count() == 3

    manager.close()

    manager = PageManager(database_path)
    manager.open()

    assert manager.page_count() == 3

    manager.close()


def test_multiple_pages_keep_independent_data(manager: PageManager):
    page1 = manager.allocate_page()
    page2 = manager.allocate_page()

    page1.write(PAGE_HEADER_SIZE, b"page one")
    page2.write(PAGE_HEADER_SIZE, b"page two")

    manager.write_page(page1)
    manager.write_page(page2)

    loaded1 = manager.read_page(0)
    loaded2 = manager.read_page(1)

    assert loaded1.read(PAGE_HEADER_SIZE, 8) == b"page one"
    assert loaded2.read(PAGE_HEADER_SIZE, 8) == b"page two"


def test_sync(manager: PageManager):
    manager.allocate_page()

    manager.sync()

    assert manager.page_count() == 1


def test_operations_require_open_manager(database_path: Path):
    manager = PageManager(database_path)

    with pytest.raises(PageManagerError):
        manager.page_count()

    with pytest.raises(PageManagerError):
        manager.read_page(0)

    with pytest.raises(PageManagerError):
        manager.allocate_page()

    with pytest.raises(PageManagerError):
        manager.sync()


def test_close_is_safe_when_called_twice(database_path: Path):
    manager = PageManager(database_path)

    manager.open()
    manager.close()
    manager.close()


def test_page_count_matches_file_size(manager: PageManager):
    for _ in range(5):
        manager.allocate_page()

    assert manager.page_count() == 5