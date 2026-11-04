"""Executes validated jobs. The only place in the runner that touches a browser."""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from gatp.inspector.locators import resolve
from gatp.runner.browser import Allowlist, BrowserOptions, open_page
from gatp.runner.jobs import InspectJob, Job, JobResult, RecountJob
from gatp.runner.sandbox import Sandbox, job_sandbox


class JobExecutor:
    """Runs one job at a time (one visible browser on screen) inside a fresh sandbox.

    All browser work happens on one dedicated worker thread: this serializes jobs and keeps
    Playwright's sync API away from any event loop the caller's thread may be running.
    """

    def __init__(self, options: BrowserOptions, sandbox_root: Path, artifacts_root: Path) -> None:
        self.options = options
        self.sandbox_root = sandbox_root
        self.artifacts_root = artifacts_root
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gatp-job")

    def run(self, job: Job) -> JobResult:
        """Run ``job`` on the worker thread and wait for its result."""
        return self._worker.submit(self._run, job).result()

    def _run(self, job: Job) -> JobResult:
        job_id = uuid.uuid4().hex[:12]
        started = time.perf_counter()
        allowlist = Allowlist(set(job.allowlist))
        with job_sandbox(self.sandbox_root, self.artifacts_root, job_id) as box:
            try:
                with open_page(self.options, allowlist, job.timeout_s) as page:
                    if isinstance(job, InspectJob):
                        files, data = self._inspect(page, job, box)
                    else:
                        files, data = self._recount(page, job)
                failed, error = False, ""
            except PlaywrightError as exc:
                files, data, failed, error = {}, {}, True, str(exc).splitlines()[0][:500]
        return JobResult(
            job_id=job_id,
            type=job.type,
            status="failed" if failed else "ok",
            duration_ms=round((time.perf_counter() - started) * 1000),
            blocked_requests=allowlist.blocked,
            files=files,
            data=data,
            error=error,
        )

    @staticmethod
    def _inspect(
        page: Page, job: InspectJob, box: Sandbox
    ) -> tuple[dict[str, str], dict[str, object]]:
        """T-006 stub: navigate, capture title + screenshot. Element extraction comes in T-007."""
        page.goto(job.url, wait_until="load")
        page.screenshot(path=box.path / "page.png", full_page=True)
        return {"screenshot": box.keep("page.png")}, {"title": page.title(), "final_url": page.url}

    @staticmethod
    def _recount(page: Page, job: RecountJob) -> tuple[dict[str, str], dict[str, object]]:
        page.goto(job.url, wait_until="load")
        counts = [resolve(page, spec).count() for spec in job.locators]
        return {}, {"counts": counts}
