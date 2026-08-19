import pytest

from book_finder.web.redirects import safe_redirect_target


@pytest.mark.parametrize(
    "target",
    [
        "/wishlist",
        "/books?title=1984&author=George+Orwell",
        "/books?title=a/b",
    ],
)
def test_site_relative_paths_are_kept(target: str) -> None:
    assert safe_redirect_target(target) == target


@pytest.mark.parametrize(
    "target",
    [
        "https://evil.example.com/phish",
        "http://evil.example.com",
        "javascript:alert(1)",
        "//evil.example.com",
        "/\\evil.example.com",
        "\\\\evil.example.com",
        "/%5Cevil.example.com",
        "books?title=1984",
        "",
        "   ",
        "/wishlist\nLocation: https://evil.example.com",
    ],
)
def test_off_site_or_malformed_targets_fall_back_to_the_wishlist(target: str) -> None:
    assert safe_redirect_target(target) == "/wishlist"
