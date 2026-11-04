"""pytest plugin the runner loads into every approved test run (``-p gatp_run_plugin``).

It is copied into the sandbox next to the generated code. It enforces the target origin
allowlist on every browser context the tests create (requests elsewhere are aborted and
recorded), so generated tests cannot reach other sites even though they run real code.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

ALLOW = set(json.loads(os.environ.get("GATP_ALLOWLIST", "[]")))
SAFE_SCHEMES = ("data:", "blob:", "about:")
BLOCKED: list[dict[str, str]] = []


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


@pytest.fixture(autouse=True)
def _gatp_allowlist(context: Any) -> None:
    def handle(route: Any) -> None:
        url = route.request.url
        if url.startswith(SAFE_SCHEMES) or _origin(url) in ALLOW:
            route.continue_()
        else:
            BLOCKED.append({"url": url, "resource_type": route.request.resource_type})
            route.abort("blockedbyclient")

    context.route("**/*", handle)


def pytest_sessionfinish(session: pytest.Session) -> None:
    out = Path("results")
    out.mkdir(exist_ok=True)
    (out / "blocked.json").write_text(json.dumps(BLOCKED), encoding="utf-8")
