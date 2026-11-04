"""Serve the BookShelf fixture site (v1 or v2) on 127.0.0.1.

Usage: ``uv run poe fixtures v1`` (or ``python fixtures/serve.py v2 --port 8090``).
Responses carry ``Cache-Control: no-store`` so switching v1 -> v2 on the same port never
shows stale pages. See fixtures/README.md for behaviors and v1 -> v2 changes.
"""

from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
VERSIONS = ("v1", "v2")
DEFAULT_PORT = 8090


class NoStoreHandler(SimpleHTTPRequestHandler):
    """Static file handler that disables caching and keeps logs short."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def site_dir(version: str) -> Path:
    """Return the directory for a fixture version, rejecting unknown versions."""
    if version not in VERSIONS:
        raise ValueError(f"unknown fixture version {version!r}; expected one of {VERSIONS}")
    return FIXTURES_DIR / f"site-{version}"


def make_server(
    version: str, port: int = DEFAULT_PORT, host: str = "127.0.0.1"
) -> ThreadingHTTPServer:
    """Build (but do not start) a server for ``version``. Port 0 picks a free port."""
    handler = functools.partial(NoStoreHandler, directory=str(site_dir(version)))
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Serve the BookShelf fixture site.")
    parser.add_argument("version", choices=VERSIONS, help="which site version to serve")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    server = make_server(args.version, args.port)
    print(f"BookShelf {args.version} on http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
