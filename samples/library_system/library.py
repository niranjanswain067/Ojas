"""Reference implementation for the Library Management System sample project."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Book:
    book_id: str
    title: str
    author: str
    copies: int = 1


@dataclass
class Member:
    member_id: str
    name: str
    borrowed_books: List[str] = field(default_factory=list)


class Library:
    """In-memory library catalog and circulation manager."""

    def __init__(self) -> None:
        self.books: Dict[str, Book] = {}
        self.members: Dict[str, Member] = {}

    def add_book(self, book_id: str, title: str, author: str, copies: int = 1) -> Book:
        if book_id in self.books:
            self.books[book_id].copies += copies
            return self.books[book_id]
        book = Book(book_id=book_id, title=title, author=author, copies=copies)
        self.books[book_id] = book
        return book

    def remove_book(self, book_id: str) -> None:
        if book_id not in self.books:
            raise KeyError(f"Book '{book_id}' not found")
        del self.books[book_id]

    def register_member(self, member_id: str, name: str) -> Member:
        if member_id in self.members:
            raise ValueError(f"Member '{member_id}' already exists")
        member = Member(member_id=member_id, name=name)
        self.members[member_id] = member
        return member

    def remove_member(self, member_id: str) -> None:
        if member_id not in self.members:
            raise KeyError(f"Member '{member_id}' not found")
        del self.members[member_id]

    def issue_book(self, book_id: str, member_id: str) -> None:
        if book_id not in self.books:
            raise KeyError(f"Book '{book_id}' not found")
        if member_id not in self.members:
            raise KeyError(f"Member '{member_id}' not found")
        book = self.books[book_id]
        if book.copies <= 0:
            raise ValueError(f"No copies available for '{book.title}'")
        book.copies -= 1
        self.members[member_id].borrowed_books.append(book_id)

    def return_book(self, book_id: str, member_id: str) -> None:
        if member_id not in self.members:
            raise KeyError(f"Member '{member_id}' not found")
        member = self.members[member_id]
        if book_id not in member.borrowed_books:
            raise ValueError(f"Book '{book_id}' not borrowed by member '{member_id}'")
        member.borrowed_books.remove(book_id)
        if book_id in self.books:
            self.books[book_id].copies += 1

    def search_books(self, query: str) -> List[Book]:
        q = query.strip().lower()
        return [
            b
            for b in self.books.values()
            if q in b.title.lower() or q in b.author.lower()
        ]

    def get_member_books(self, member_id: str) -> List[str]:
        if member_id not in self.members:
            raise KeyError(f"Member '{member_id}' not found")
        return list(self.members[member_id].borrowed_books)

    def inventory_summary(self) -> Dict[str, int]:
        return {
            "unique_titles": len(self.books),
            "available_copies": sum(b.copies for b in self.books.values()),
        }
