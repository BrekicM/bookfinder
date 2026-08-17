import re
import unicodedata

# Đ/đ (D with stroke) has no Unicode decomposition, so NFKD alone won't strip it.
_EXTRA_CHARS = str.maketrans({"đ": "d", "Đ": "D"})


def slugify(text: str) -> str:
    text = text.translate(_EXTRA_CHARS)
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = without_marks.lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", lowered)).strip("-")
