import httpx
from fastapi import Request

USER_AGENT = "Mozilla/5.0 (compatible; BookFinder/0.1; personal use)"

HEADERS = {"User-Agent": USER_AGENT}


def create_http_client() -> httpx.AsyncClient:
    """The one outbound client the app owns for its whole lifetime.

    Pooled: every route shares it, so repeated requests to the same handful
    of Bookstores reuse existing TCP+TLS connections instead of handshaking
    again per request. Identifying: every outbound request carries the same
    polite User-Agent, in keeping with ADR 0008's stance on scraping etiquette.
    """
    return httpx.AsyncClient(headers=HEADERS, follow_redirects=True)


def get_http_client(request: Request) -> httpx.AsyncClient:
    """FastAPI dependency handing routes the app-owned client.

    Deliberately has no fallback: if this raises, the app was started without
    its lifespan, and a per-request client silently created here would quietly
    undo the pooling. Tests use the ``client`` fixture, which runs lifespan.
    """
    return request.app.state.http_client
