"""`gatp-api` entrypoint: serve the FastAPI app with uvicorn."""

import argparse

import uvicorn

from gatp.config import get_settings


def main(argv: list[str] | None = None) -> None:
    """Parse CLI flags and start uvicorn."""
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="gatp-api", description="Run the GATP API server.")
    parser.add_argument("--host", default=settings.api_host)
    parser.add_argument("--port", type=int, default=settings.api_port)
    parser.add_argument("--reload", action="store_true", help="Reload on code changes (dev).")
    args = parser.parse_args(argv)
    uvicorn.run(
        "gatp.api.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
