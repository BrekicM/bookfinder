"""Validation for user-supplied post-action redirect targets.

The wishlist forms carry a ``next`` field so the user lands back where they
came from. That value reaches us from the browser, so it is only ever allowed
to be a site-relative path — anything that could send the user to another
origin falls back to a safe default.
"""

from urllib.parse import unquote

DEFAULT_REDIRECT = "/wishlist"


def safe_redirect_target(target: str, default: str = DEFAULT_REDIRECT) -> str:
    """Return ``target`` if it is a safe site-relative path, else ``default``.

    Rejects absolute URLs, scheme-relative (``//host``) and backslash variants
    (``/\\host``, ``\\\\host``, percent-encoded forms of either), paths without
    a leading slash, and anything carrying whitespace or control characters.
    """
    if not target or any(char.isspace() or ord(char) < 0x20 for char in target):
        return default

    normalized = unquote(target).replace("\\", "/")
    if not normalized.startswith("/") or normalized.startswith("//"):
        return default

    return target
