from fastapi.testclient import TestClient


def test_home_page_brand_is_not_a_back_link(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert '<a href="/" class="brand">' not in response.text
    assert "Book Finder" in response.text


def test_other_pages_still_show_the_back_link_to_home(client: TestClient) -> None:
    response = client.get("/wishlist")

    assert response.status_code == 200
    assert '<a href="/" class="brand">' in response.text
