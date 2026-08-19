# Test list:
# - home page defaults to English with no lang param/cookie
# - ?lang=sr-latn on home page shows Serbian Latin UI text
# - ?lang=sr-cyrl on home page shows transliterated Cyrillic UI text
# - a valid ?lang= sets a "lang" cookie on the response
# - a previously-set cookie is honored on a later request with no lang param
# - genre labels on the home page are translated
# - the wishlist page picks up the same language switching

from fastapi.testclient import TestClient

from book_finder.config import settings


def test_home_page_defaults_to_english(client: TestClient) -> None:
    response = client.get("/")

    assert "Browse by genre" in response.text


def test_home_page_shows_serbian_latin_when_requested(client: TestClient) -> None:
    response = client.get("/?lang=sr-latn")

    assert "Pregled po žanru" in response.text


def test_home_page_shows_transliterated_cyrillic_when_requested(client: TestClient) -> None:
    response = client.get("/?lang=sr-cyrl")

    assert "Претрага" in response.text


def test_valid_lang_param_sets_a_cookie(client: TestClient) -> None:
    response = client.get("/?lang=sr-latn")

    assert response.cookies.get("lang") == "sr-latn"


def test_cookie_is_honored_on_a_later_request_with_no_param(client: TestClient) -> None:
    client.cookies.set("lang", "sr-cyrl")

    response = client.get("/")

    assert "Претрага" in response.text
    client.cookies.clear()


def test_genre_labels_on_home_page_are_translated(client: TestClient) -> None:
    response = client.get("/?lang=sr-latn")

    assert "Fantastika" in response.text


def test_wishlist_page_follows_the_same_language_switching(
    client: TestClient, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "wishlist_file", tmp_path / "wishlist.json")

    response = client.get("/wishlist?lang=sr-latn")

    assert "Lista želja" in response.text
