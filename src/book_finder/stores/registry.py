from book_finder.stores.base import BookstoreClient
from book_finder.stores.delfi import DelfiClient
from book_finder.stores.laguna import LagunaClient
from book_finder.stores.vulkan import VulkanClient

_laguna = LagunaClient()
_vulkan = VulkanClient()
_delfi = DelfiClient()

ACTIVE_CLIENTS: list[BookstoreClient] = [_laguna, _vulkan, _delfi]

# Laguna/Vulkan have no live search API (see BookstoreClient's docstring), so
# free-text search matches against their cached catalogs instead. Delfi is
# excluded here — it has a real search API, used directly (see store_search.py).
CATALOG_SEARCH_CLIENTS: list[BookstoreClient] = [_laguna, _vulkan]
