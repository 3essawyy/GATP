"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from gatp.api.app import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient for a fresh app instance."""
    with TestClient(create_app()) as c:
        yield c
