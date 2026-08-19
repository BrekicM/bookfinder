import pytest
from fastapi.testclient import TestClient

from book_finder.config import settings


def test_wishlist_page_is_empty_by_default(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    response = client.get("/wishlist")

    assert response.status_code == 200
    assert "1984" not in response.text


def test_add_then_view_wishlist_shows_the_book(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    client.post("/wishlist/add", data={"title": "1984", "author": "George Orwell"})
    response = client.get("/wishlist")

    assert response.status_code == 200
    assert "1984" in response.text
    assert "George Orwell" in response.text


def test_remove_takes_it_off_the_wishlist_page(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    client.post("/wishlist/add", data={"title": "1984", "author": "George Orwell"})
    client.post("/wishlist/remove", data={"title": "1984", "author": "George Orwell"})
    response = client.get("/wishlist")

    assert "1984" not in response.text


def test_add_redirects_to_the_given_next_url(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    response = client.post(
        "/wishlist/add",
        data={
            "title": "1984",
            "author": "George Orwell",
            "next": "/books?title=1984&author=George+Orwell",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/books?title=1984&author=George+Orwell"


OFF_SITE_TARGETS = [
    "https://evil.example.com/phish",
    "//evil.example.com",
    "/\\evil.example.com",
    "\\\\evil.example.com",
    "books?title=1984",
]


@pytest.mark.parametrize("target", OFF_SITE_TARGETS)
def test_add_refuses_to_redirect_off_site(
    client: TestClient, target, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    response = client.post(
        "/wishlist/add",
        data={"title": "1984", "author": "George Orwell", "next": target},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/wishlist"


@pytest.mark.parametrize("target", OFF_SITE_TARGETS)
def test_remove_refuses_to_redirect_off_site(
    client: TestClient, target, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    response = client.post(
        "/wishlist/remove",
        data={"title": "1984", "author": "George Orwell", "next": target},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/wishlist"
