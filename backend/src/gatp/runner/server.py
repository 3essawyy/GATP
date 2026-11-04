"""The runner's HTTP API, served only on a Unix domain socket (ADR-017).

Endpoints: ``GET /health`` and ``POST /jobs``. A malformed or unknown job is rejected by
Pydantic with HTTP 422 before anything runs. There is no endpoint that accepts code or commands.
"""

from __future__ import annotations

from fastapi import FastAPI

from gatp import __version__
from gatp.runner.executor import JobExecutor
from gatp.runner.jobs import JobRequest, JobResult


def create_runner_app(executor: JobExecutor) -> FastAPI:
    app = FastAPI(title="GATP runner", version=__version__, docs_url=None, redoc_url=None)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "headless": str(executor.options.headless).lower()}

    @app.post("/jobs")
    def submit(request: JobRequest) -> JobResult:
        # Sync endpoint: FastAPI runs it in a worker thread; the executor serializes jobs.
        return executor.run(request.job)

    return app
