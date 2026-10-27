from __future__ import annotations

import pytest

from pykd.page import (
    PAGE_HEADER_SIZE,
    PAGE_SIZE,
    PAGE_TYPE_DATA,
    Page,
    PageError,
)


def test_page_has_correct_size():
    page = Page(page_id=0)

    assert len(page.data) == PAGE_SIZE
    assert PAGE_SIZE == 4096


def test_page_has_correct_header_size():
    assert PAGE_HEADER_SIZE == 8


def test_page_initializes_correctly():
    page = Page(page_id=5)

    assert page.page_id == 5
    assert page.page_type == PAGE_TYPE_DATA
    assert page.is_empty()


def test_page_rejects_negative_page_id():
    with pytest.raises(ValueError):
        Page(page_id=-1)


def test_page_write_and_read():
    page = Page(page_id=0)

    data = b"hello PyKD"

    page.write(PAGE_HEADER_SIZE, data)

    assert page.read(PAGE_HEADER_SIZE, len(data)) == data


def test_page_can_store_binary_data():
    page = Page(page_id=1)

    data = bytes(range(256))

    page.write(PAGE_HEADER_SIZE, data)

    assert page.read(
        PAGE_HEADER_SIZE,
        len(data),
    ) == data


def test_page_write_cannot_overflow():
    page = Page(page_id=0)

    data = b"x" * (PAGE_SIZE - PAGE_HEADER_SIZE + 1)

    with pytest.raises(PageError):
        page.write(PAGE_HEADER_SIZE, data)


def test_page_read_cannot_overflow():
    page = Page(page_id=0)

    with pytest.raises(PageError):
        page.read(
            PAGE_HEADER_SIZE,
            PAGE_SIZE,
        )


def test_page_cannot_write_into_header():
    page = Page(page_id=0)

    with pytest.raises(PageError):
        page.write(0, b"test")


def test_page_cannot_read_from_header():
    page = Page(page_id=0)

    with pytest.raises(PageError):
        page.read(0, 4)


def test_page_rejects_negative_read_length():
    page = Page(page_id=0)

    with pytest.raises(ValueError):
        page.read(PAGE_HEADER_SIZE, -1)


def test_page_serialize_has_exact_page_size():
    page = Page(page_id=42)

    serialized = page.serialize()

    assert len(serialized) == PAGE_SIZE


def test_page_serialization_preserves_metadata():
    page = Page(
        page_id=42,
        page_type=PAGE_TYPE_DATA,
    )

    raw = page.serialize()
    restored = Page.deserialize(raw)

    assert restored.page_id == 42
    assert restored.page_type == PAGE_TYPE_DATA


def test_page_serialization_preserves_data():
    page = Page(page_id=10)

    data = b"PyKD database engine"

    page.write(PAGE_HEADER_SIZE, data)

    raw = page.serialize()

    restored = Page.deserialize(raw)

    assert restored.read(
        PAGE_HEADER_SIZE,
        len(data),
    ) == data


def test_page_deserialize_rejects_invalid_size():
    with pytest.raises(PageError):
        Page.deserialize(b"invalid")


def test_page_clear_removes_data():
    page = Page(page_id=0)

    page.write(PAGE_HEADER_SIZE, b"PyKD")

    assert not page.is_empty()

    page.clear()

    assert page.is_empty()


def test_page_usable_size():
    page = Page(page_id=0)

    assert page.usable_size == PAGE_SIZE - PAGE_HEADER_SIZE
    assert page.usable_size == 4088