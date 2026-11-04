"""TC-106: the runner is a separate process on a private Unix socket; API client talks to it."""

import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from gatp.runner.client import RunnerClient, RunnerRejectedError, RunnerUnavailableError
from gatp.runner.jobs import InspectJob


@pytest.fixture(scope="module")
def runner(tmp_path_factory: pytest.TempPathFactory) -> object:
    base = tmp_path_factory.mktemp("runner")
    sock = base / "run" / "runner.sock"
    env = {
        **os.environ,
        "GATP_RUNNER_SOCKET": str(sock),
        "GATP_RUNNER_HEADLESS": "true",
        "GATP_RUNNER_SANDBOX_DIR": str(base / "sandbox"),
        "GATP_ARTIFACTS_DIR": str(base / "artifacts"),
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "gatp.runner.main"], env=env, stderr=subprocess.PIPE, text=True
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            RunnerClient(sock, timeout_s=2).health()
            break
        except (RunnerUnavailableError, OSError):
            time.sleep(0.1)
    yield sock, base
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_socket_is_private(runner: tuple[Path, Path]) -> None:
    sock, _ = runner
    mode = sock.stat().st_mode
    assert stat.S_ISSOCK(mode)
    assert mode & 0o777 == 0o600
    assert sock.parent.stat().st_mode & 0o777 == 0o700


def test_health_and_inspect_over_socket(runner: tuple[Path, Path], site_v1: str) -> None:
    sock, base = runner
    client = RunnerClient(sock)
    assert client.health()["headless"] == "true"
    result = client.submit(InspectJob(url=f"{site_v1}/index.html", allowlist=[site_v1]))
    assert result.status == "ok", result.error
    assert (base / "artifacts" / result.files["screenshot"]).exists()


def test_runner_rejects_unknown_and_disallowed_jobs(runner: tuple[Path, Path]) -> None:
    client = RunnerClient(runner[0])
    assert client.submit_raw({"job": {"type": "shell", "cmd": "id"}}).status_code == 422
    assert (
        client.submit_raw(
            {"job": {"type": "inspect", "url": "http://evil.test/", "allowlist": ["http://a.b"]}}
        ).status_code
        == 422
    )
    with pytest.raises(RunnerRejectedError):
        client.submit(
            InspectJob.model_construct(
                type="inspect", url="http://evil.test/", allowlist=["http://a.b"], timeout_s=5
            )
        )


def test_client_reports_missing_runner(tmp_path: Path) -> None:
    with pytest.raises(RunnerUnavailableError, match="poe runner"):
        RunnerClient(tmp_path / "nope.sock").submit(
            InspectJob(url="http://a.b/", allowlist=["http://a.b"])
        )
