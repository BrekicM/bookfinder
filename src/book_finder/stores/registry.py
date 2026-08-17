from book_finder.stores.base import BookstoreClient
from book_finder.stores.laguna import LagunaClient
from book_finder.stores.vulkan import VulkanClient

ACTIVE_CLIENTS: list[BookstoreClient] = [LagunaClient(), VulkanClient()]
