import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _path_for(cache_dir: Path, key: str) -> Path:
    safe_key = re.sub(r"[^a-zA-Z0-9_-]+", "_", key)
    return cache_dir / f"{safe_key}.json"


def write_cache(cache_dir: Path, key: str, data: Any, *, now: datetime | None = None) -> None:
    now = now or datetime.now(UTC)
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": now.isoformat(), "data": data}
    _path_for(cache_dir, key).write_text(json.dumps(payload), encoding="utf-8")


def read_stale(cache_dir: Path, key: str, *, now: datetime | None = None) -> Any | None:
    path = _path_for(cache_dir, key)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["data"]


def read_cache(
    cache_dir: Path, key: str, *, max_age: timedelta, now: datetime | None = None
) -> Any | None:
    path = _path_for(cache_dir, key)
    if not path.exists():
        return None

    now = now or datetime.now(UTC)
    payload = json.loads(path.read_text(encoding="utf-8"))
    fetched_at = datetime.fromisoformat(payload["fetched_at"])
    if now - fetched_at > max_age:
        return None
    return payload["data"]
