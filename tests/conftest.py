from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from book_finder.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient that actually runs the app's lifespan.

    A bare ``TestClient(app)`` never starts lifespan, so the pooled
    ``app.state.http_client`` created on startup would not exist. Using the
    context-manager form is the fix; every route test goes through this
    fixture so no test can accidentally exercise a half-started app.
    """
    with TestClient(app) as test_client:
        yield test_client
