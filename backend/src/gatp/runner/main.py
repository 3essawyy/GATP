"""`gatp-runner` entrypoint (stub).

The runner is a separate process from the API (ADR-004). In T-002 it only proves that the
process can be started on its own: it logs that it is ready and idles until stopped.
T-006 adds the typed job protocol, sandbox directories, origin allowlist and headed browser.
"""

import logging
import signal
import threading
from types import FrameType

from gatp.config import get_settings

log = logging.getLogger("gatp.runner")


def run(stop: threading.Event) -> None:
    """Idle until ``stop`` is set. Separated from ``main`` so tests can drive it."""
    log.info("runner ready (no jobs yet; job protocol arrives in T-006)")
    while not stop.wait(timeout=0.5):
        pass
    log.info("runner stopped")


def main() -> None:
    """Configure logging, install signal handlers and run until Ctrl+C / SIGTERM."""
    logging.basicConfig(
        level=get_settings().log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    stop = threading.Event()

    def _handle(signum: int, _frame: FrameType | None) -> None:
        log.info("received signal %s, shutting down", signum)
        stop.set()

    signal.signal(signal.SIGINT, _handle)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle)
    run(stop)


if __name__ == "__main__":  # pragma: no cover
    main()
