"""Test suite for Library Management System sample project."""

import pytest
from library import Library


def test_add_and_remove_book():
    lib = Library()
    lib.add_book("B1", "Clean Code", "Robert Martin", copies=2)
    assert lib.inventory_summary()["unique_titles"] == 1
    assert lib.inventory_summary()["available_copies"] == 2
    lib.remove_book("B1")
    assert lib.inventory_summary()["unique_titles"] == 0
    with pytest.raises(KeyError):
        lib.remove_book("B1")


def test_register_and_remove_member():
    lib = Library()
    lib.register_member("M1", "Alice")
    with pytest.raises(ValueError):
        lib.register_member("M1", "Alice Duplicate")
    lib.remove_member("M1")
    with pytest.raises(KeyError):
        lib.remove_member("M1")


def test_issue_and_return_book():
    lib = Library()
    lib.add_book("B1", "Clean Code", "Robert Martin", copies=1)
    lib.register_member("M1", "Alice")
    lib.register_member("M2", "Bob")

    lib.issue_book("B1", "M1")
    assert lib.books["B1"].copies == 0
    assert lib.get_member_books("M1") == ["B1"]

    with pytest.raises(ValueError):
        lib.issue_book("B1", "M2")

    lib.return_book("B1", "M1")
    assert lib.books["B1"].copies == 1
    assert lib.get_member_books("M1") == []


def test_search_books():
    lib = Library()
    lib.add_book("B1", "Python Crash Course", "Eric Matthes")
    lib.add_book("B2", "Fluent Python", "Luciano Ramalho")
    results = lib.search_books("python")
    assert len(results) == 2
    assert len(lib.search_books("ramalho")) == 1
