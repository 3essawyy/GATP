"""Browser sessions with an origin allowlist enforced by Playwright routing (ADR-004).

Every request the page makes passes through ``route("**/*")``. Requests to origins outside the
job's allowlist are aborted and recorded, so the page under test can't reach other sites.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from playwright.sync_api import Page, Route, sync_playwright

from gatp.runner.jobs import BlockedRequest, origin

ALWAYS_ALLOWED_SCHEMES = ("data:", "blob:", "about:")


@dataclass
class Allowlist:
    origins: set[str]
    blocked: list[BlockedRequest] = field(default_factory=list)

    def allows(self, url: str) -> bool:
        if url.startswith(ALWAYS_ALLOWED_SCHEMES):
            return True
        try:
            return origin(url) in self.origins
        except ValueError:
            return False

    def handle(self, route: Route) -> None:
        request = route.request
        if self.allows(request.url):
            route.continue_()
        else:
            self.blocked.append(
                BlockedRequest(url=request.url, resource_type=request.resource_type)
            )
            route.abort("blockedbyclient")


@dataclass(frozen=True)
class BrowserOptions:
    headless: bool = False
    executable_path: str = ""
    slow_mo_ms: int = 0
    viewport: tuple[int, int] = (1280, 800)


@contextmanager
def open_page(options: BrowserOptions, allowlist: Allowlist, timeout_s: float) -> Iterator[Page]:
    """Launch Chromium (headed unless ``headless``), apply the allowlist, yield a fresh page."""
    launch: dict[str, Any] = {"headless": options.headless, "slow_mo": options.slow_mo_ms}
    if options.executable_path:
        launch["executable_path"] = options.executable_path
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        try:
            context = browser.new_context(
                viewport={"width": options.viewport[0], "height": options.viewport[1]},
                service_workers="block",  # service workers could bypass routing
            )
            context.route("**/*", allowlist.handle)
            page = context.new_page()
            page.set_default_timeout(timeout_s * 1000)
            yield page
            context.close()
        finally:
            browser.close()
