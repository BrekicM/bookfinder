from datetime import UTC, datetime, timedelta

from book_finder.popularity.cache import read_cache, read_stale, write_cache


def test_read_cache_returns_none_when_missing(tmp_path) -> None:
    assert read_cache(tmp_path, "missing-key", max_age=timedelta(hours=1)) is None


def test_write_then_read_returns_the_data(tmp_path) -> None:
    write_cache(tmp_path, "key", {"hello": "world"})
    assert read_cache(tmp_path, "key", max_age=timedelta(hours=1)) == {"hello": "world"}


def test_read_cache_returns_none_when_stale(tmp_path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    write_cache(tmp_path, "key", {"a": 1}, now=now)

    later = now + timedelta(hours=2)
    assert read_cache(tmp_path, "key", max_age=timedelta(hours=1), now=later) is None


def test_read_cache_returns_data_when_within_max_age(tmp_path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    write_cache(tmp_path, "key", {"a": 1}, now=now)

    later = now + timedelta(minutes=30)
    assert read_cache(tmp_path, "key", max_age=timedelta(hours=1), now=later) == {"a": 1}


def test_read_stale_returns_data_regardless_of_age(tmp_path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    write_cache(tmp_path, "key", {"a": 1}, now=now)

    assert read_stale(tmp_path, "key") == {"a": 1}


def test_read_stale_returns_none_when_missing(tmp_path) -> None:
    assert read_stale(tmp_path, "missing-key") is None
