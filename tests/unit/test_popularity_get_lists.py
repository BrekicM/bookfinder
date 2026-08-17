from datetime import timedelta

import httpx
import pytest

from book_finder.domain.models import Genre
from book_finder.popularity.service import get_lists


@pytest.mark.asyncio
async def test_serbian_list_is_unavailable_without_a_network_call_for_unmapped_genre(
    tmp_path,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "laguna" in url or "knjizare-vulkan" in url:
            # Programming/Tech has no Serbian source at all — if this handler
            # is ever hit for it, something is fetching data that
            # genre_mapping says doesn't exist.
            raise AssertionError(f"unexpected Serbian-source call to {url}")
        return httpx.Response(200, json={"works": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        _global_list, serbian_list = await get_lists(
            Genre.PROGRAMMING_TECH, client, cache_dir=tmp_path, cache_ttl=timedelta(hours=1)
        )

    assert serbian_list.available is False
    assert serbian_list.entries == []
    assert serbian_list.scope == "serbian"
