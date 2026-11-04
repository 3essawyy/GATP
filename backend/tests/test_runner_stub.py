"""The runner is its own process (ADR-004); the T-002 stub starts and stops cleanly."""

import logging
import signal
import subprocess
import sys
import threading
import time

import pytest

from gatp.runner.main import run


def test_run_logs_ready_and_stops(caplog: pytest.LogCaptureFixture) -> None:
    stop = threading.Event()
    caplog.set_level(logging.INFO, logger="gatp.runner")
    t = threading.Thread(target=run, args=(stop,))
    t.start()
    stop.set()
    t.join(timeout=5)
    assert not t.is_alive()
    assert "runner ready" in caplog.text
    assert "runner stopped" in caplog.text


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signal delivery")
def test_entrypoint_runs_as_separate_process() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "gatp.runner.main"],
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(1.5)
        assert proc.poll() is None, "runner exited early"
        proc.send_signal(signal.SIGTERM)
        _, err = proc.communicate(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == 0
    assert "runner ready" in err
