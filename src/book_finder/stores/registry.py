from book_finder.stores.base import BookstoreClient
from book_finder.stores.booka import BookaClient
from book_finder.stores.delfi import DelfiClient
from book_finder.stores.laguna import LagunaClient
from book_finder.stores.vulkan import VulkanClient

_laguna = LagunaClient()
_vulkan = VulkanClient()
_delfi = DelfiClient()
_booka = BookaClient()

ACTIVE_CLIENTS: list[BookstoreClient] = [_laguna, _vulkan, _delfi, _booka]

# Laguna/Vulkan have no live search API (see BookstoreClient's docstring), so
# free-text search matches against their cached catalogs instead. Delfi and
# Booka are excluded here — both have their own real search APIs, used
# directly (see store_search.py).
CATALOG_SEARCH_CLIENTS: list[BookstoreClient] = [_laguna, _vulkan]
