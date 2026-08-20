from book_finder.stores.base import BookstoreClient
from book_finder.stores.booka import BookaClient
from book_finder.stores.carobna_knjiga import CarobnaKnjigaClient
from book_finder.stores.delfi import DelfiClient
from book_finder.stores.geopoetika import GeopoetikaClient
from book_finder.stores.laguna import LagunaClient
from book_finder.stores.vulkan import VulkanClient

_laguna = LagunaClient()
_vulkan = VulkanClient()
_delfi = DelfiClient()
_booka = BookaClient()
_carobna_knjiga = CarobnaKnjigaClient()
_geopoetika = GeopoetikaClient()

# Every client satisfies the same BookstoreClient contract (find_editions +
# search_titles), whether it reaches its store via a real search API (Delfi,
# Booka) or a cached catalog (Laguna, Vulkan, Čarobna knjiga, Geopoetika), so
# search and the live-check page iterate this one list.
ACTIVE_CLIENTS: list[BookstoreClient] = [
    _laguna,
    _vulkan,
    _delfi,
    _booka,
    _carobna_knjiga,
    _geopoetika,
]
