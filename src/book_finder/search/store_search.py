from book_finder.domain.models import Book


def books_to_search_dicts(books: list[Book]) -> list[dict]:
    return [
        {
            "title": book.title,
            "author_name": [book.author] if book.author else [],
        }
        for book in books
    ]
