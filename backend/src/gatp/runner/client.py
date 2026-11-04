"""API-side client for the runner (imported by ``gatp.api`` only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from pydantic import TypeAdapter

from gatp.runner.jobs import Job, JobResult


class RunnerUnavailableError(RuntimeError):
    """The runner process is not running or its socket is missing."""


class RunnerRejectedError(ValueError):
    """The runner refused the job (validation error)."""


class RunnerClient:
    """Submits typed jobs over the runner's Unix socket."""

    def __init__(self, socket: Path, timeout_s: float = 300.0) -> None:
        self.socket = socket
        self._client = httpx.Client(
            transport=httpx.HTTPTransport(uds=str(socket)),
            base_url="http://runner",
            timeout=timeout_s,
        )

    def health(self) -> dict[str, Any]:
        try:
            resp = self._client.get("/health")
        except httpx.TransportError as exc:
            raise RunnerUnavailableError(f"runner not reachable at {self.socket}") from exc
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    def submit(self, job: Job) -> JobResult:
        # Serialize only: the runner itself validates (and may reject) the job.
        payload = {"job": job.model_dump(mode="json")}
        try:
            resp = self._client.post("/jobs", json=payload)
        except httpx.TransportError as exc:
            raise RunnerUnavailableError(
                f"runner not reachable at {self.socket}; start it with `uv run poe runner`"
            ) from exc
        if resp.status_code == 422:
            raise RunnerRejectedError(resp.text)
        resp.raise_for_status()
        return JobResult.model_validate(resp.json())

    def submit_raw(self, payload: dict[str, Any]) -> httpx.Response:
        """Send an arbitrary payload (used by tests to prove the runner rejects it)."""
        return self._client.post("/jobs", json=payload)


JOB_ADAPTER: TypeAdapter[Job] = TypeAdapter(Job)
