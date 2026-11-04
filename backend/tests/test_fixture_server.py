"""TC-103: the fixture server serves the right version and disables caching."""

import urllib.request

import pytest

from .conftest import fixture_serve


def test_unknown_version_rejected() -> None:
    with pytest.raises(ValueError, match="unknown fixture version"):
        fixture_serve.site_dir("v3")


@pytest.mark.parametrize(("fixture_name", "version"), [("site_v1", "v1"), ("site_v2", "v2")])
def test_serves_version_without_cache(
    request: pytest.FixtureRequest, fixture_name: str, version: str
) -> None:
    base: str = request.getfixturevalue(fixture_name)
    with urllib.request.urlopen(f"{base}/index.html") as resp:  # noqa: S310 - local test server
        body = resp.read().decode()
        assert resp.headers["Cache-Control"] == "no-store"
    assert f"BookShelf fixture site · {version}" in body
