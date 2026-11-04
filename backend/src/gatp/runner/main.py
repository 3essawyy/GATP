"""`gatp-runner` entrypoint: serve typed jobs on a Unix socket (ADR-004, ADR-017).

The runner is a separate process from the API. It listens on ``GATP_RUNNER_SOCKET``
(default ``data/runner/runner.sock``). The socket is bound here, set to mode 0600 inside a
0700 directory, and handed to uvicorn, so only this OS user can submit jobs. There is no
TCP port.
"""

from __future__ import annotations

import logging
import os
import socket as sockets
from pathlib import Path

import uvicorn

from gatp.config import Settings, get_settings
from gatp.runner.browser import BrowserOptions
from gatp.runner.executor import JobExecutor
from gatp.runner.server import create_runner_app

log = logging.getLogger("gatp.runner")


def build_executor(settings: Settings) -> JobExecutor:
    return JobExecutor(
        BrowserOptions(
            headless=settings.runner_headless,
            executable_path=settings.chromium_executable,
            slow_mo_ms=settings.runner_slow_mo_ms,
        ),
        sandbox_root=settings.runner_sandbox_dir,
        artifacts_root=settings.artifacts_dir,
    )


def bind_private_socket(path: Path) -> sockets.socket:
    """Bind a Unix socket at ``path`` with mode 0600 in a 0700 directory.

    A stale socket left by a crashed runner is removed first.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    if path.exists() or path.is_symlink():
        path.unlink()
    sock = sockets.socket(sockets.AF_UNIX, sockets.SOCK_STREAM)
    sock.bind(str(path))
    os.chmod(path, 0o600)
    return sock


def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    path = settings.runner_socket
    sock = bind_private_socket(path)
    mode = "headless (CI)" if settings.runner_headless else "headed (visible browser)"
    log.info("runner ready on unix socket %s, %s", path, mode)
    config = uvicorn.Config(
        create_runner_app(build_executor(settings)), log_level=settings.log_level.lower()
    )
    try:
        uvicorn.Server(config).run(sockets=[sock])
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":  # pragma: no cover
    main()
