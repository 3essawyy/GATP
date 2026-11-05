"""Executes validated jobs. The only place in the runner that touches a browser."""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from gatp.inspector.inspect import inspect_page
from gatp.inspector.locators import resolve
from gatp.runner.browser import Allowlist, BrowserOptions, open_page
from gatp.runner.collect import collect
from gatp.runner.execute import IsolationUnavailableError, RunOptions, run_tests
from gatp.runner.jobs import (
    CollectJob,
    InspectJob,
    Job,
    JobResult,
    RecountJob,
    RunTestsJob,
    SetupStep,
    origin,
)
from gatp.runner.sandbox import Sandbox, job_sandbox


class JobExecutor:
    """Runs one job at a time (one visible browser on screen) inside a fresh sandbox.

    All browser work happens on one dedicated worker thread: this serializes jobs and keeps
    Playwright's sync API away from any event loop the caller's thread may be running.
    """

    def __init__(
        self,
        options: BrowserOptions,
        sandbox_root: Path,
        artifacts_root: Path,
        isolation: str = "bwrap",
        hide: tuple[Path, ...] = (),
    ) -> None:
        self.options = options
        self.isolation = isolation
        self.hide = hide
        self.sandbox_root = sandbox_root
        self.artifacts_root = artifacts_root
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gatp-job")

    def run_options(self) -> RunOptions:
        return RunOptions(
            isolation=self.isolation,
            headless=self.options.headless,
            chromium_executable=self.options.executable_path,
            slow_mo_ms=self.options.slow_mo_ms,
            hide=self.hide,
        )

    def run(self, job: Job) -> JobResult:
        """Run ``job`` on the worker thread and wait for its result."""
        return self._worker.submit(self._run, job).result()

    def _run(self, job: Job) -> JobResult:
        job_id = uuid.uuid4().hex[:12]
        started = time.perf_counter()
        if isinstance(job, RunTestsJob):
            with job_sandbox(self.sandbox_root, self.artifacts_root, job_id) as box:
                try:
                    data = run_tests(job, box.path, self.run_options())
                    error = "timed out" if data["timed_out"] else ""
                except IsolationUnavailableError as exc:
                    data, error = {}, str(exc)
                files = {}
                results_dir = box.path / "results"
                if results_dir.exists():
                    for f in sorted(results_dir.rglob("*")):
                        if f.is_file() and f.suffix in (".png", ".xml", ".json"):
                            rel = f.relative_to(box.path).as_posix()
                            files[rel] = box.keep(rel)
                for r in data.get("results", []):
                    r["screenshots"] = [files[s] for s in r["screenshots"] if s in files]
            return JobResult(
                job_id=job_id,
                type=job.type,
                status="failed" if error else "ok",
                duration_ms=round((time.perf_counter() - started) * 1000),
                files={k: v for k, v in files.items() if not k.endswith(".png")},
                data=data,
                error=error,
            )
        if isinstance(job, CollectJob):
            with job_sandbox(self.sandbox_root, self.artifacts_root, job_id) as box:
                data, failed, error = collect(job, box.path)
            return JobResult(
                job_id=job_id,
                type=job.type,
                status="failed" if failed else "ok",
                duration_ms=round((time.perf_counter() - started) * 1000),
                data=data,
                error=error,
            )
        allowlist = Allowlist(set(job.allowlist))
        with job_sandbox(self.sandbox_root, self.artifacts_root, job_id) as box:
            try:
                with open_page(self.options, allowlist, job.timeout_s) as page:
                    if isinstance(job, InspectJob):
                        files, data = self._inspect(page, job, box)
                    else:
                        files, data = self._recount(page, job)
                failed, error = False, ""
            except SetupStepError as exc:
                files, failed, error = {}, True, str(exc)[:500]
                data = {"failed_setup_step": exc.step}
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
        """Run setup steps, open the page, inspect it, keep screenshot + served HTML."""
        _run_setup(page, job.setup)
        page.goto(job.url, wait_until="load")
        page.wait_for_timeout(300)  # let onload scripts (e.g. client-side redirects) run
        page.wait_for_load_state("load")
        if origin(page.url) not in job.allowlist:
            raise PlaywrightError(f"redirected outside the allowlist to {page.url}")
        # The served source of the page we ended on (for source-line links), same cookies.
        html = page.request.get(page.url).text()
        result = inspect_page(page, html, job.scope, url=job.url)
        page.screenshot(path=box.path / "page.png", full_page=True)
        (box.path / "page.html").write_text(html, encoding="utf-8")
        files = {"screenshot": box.keep("page.png"), "html": box.keep("page.html")}
        return files, result.model_dump(mode="json")

    @staticmethod
    def _recount(page: Page, job: RecountJob) -> tuple[dict[str, str], dict[str, object]]:
        _run_setup(page, job.setup)
        page.goto(job.url, wait_until="load")
        counts = [resolve(page, spec).count() for spec in job.locators]
        return {}, {"counts": counts}


SETUP_ACTION_TIMEOUT_MS = 10_000


class SetupStepError(PlaywrightError):
    """A tester-approved setup step failed (e.g. its locator no longer matches, T-016)."""

    def __init__(self, step: int, message: str) -> None:
        super().__init__(message)
        self.step = step


def _run_setup(page: Page, steps: list[SetupStep]) -> None:
    for n, step in enumerate(steps, 1):
        try:
            _run_step(page, step)
        except PlaywrightError as exc:
            target = (
                step.url
                if step.action == "goto"
                else step.locator.to_python()
                if step.locator
                else ""
            )
            first = str(exc).splitlines()[0][:300]
            raise SetupStepError(
                n, f"setup step {n} ({step.action} {target}) failed: {first}"
            ) from exc


def _run_step(page: Page, step: SetupStep) -> None:
    """Execute one setup step. Steps are data; only these four actions exist."""
    if step.action == "goto":
        page.goto(step.url, wait_until="load")
        return
    if step.locator is None:  # pragma: no cover - prevented by SetupStep validation
        raise ValueError(f"{step.action} needs a locator")
    target = resolve(page, step.locator)
    if step.action == "fill":
        target.fill(step.value, timeout=SETUP_ACTION_TIMEOUT_MS)
    elif step.action == "click":
        target.click(timeout=SETUP_ACTION_TIMEOUT_MS)
        page.wait_for_load_state("load")
    else:
        target.select_option(step.value, timeout=SETUP_ACTION_TIMEOUT_MS)
