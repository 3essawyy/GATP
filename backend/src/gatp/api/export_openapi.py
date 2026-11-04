"""Write the API's OpenAPI schema to a file without starting a server.

Usage: ``python -m gatp.api.export_openapi frontend/openapi.json``
(wrapped by ``uv run poe gen-client``, which then regenerates the TS types).
"""

import json
import sys
from pathlib import Path
from typing import Any

from gatp.api.app import create_app


def openapi_schema() -> dict[str, Any]:
    """Return the OpenAPI schema as a dict."""
    return create_app().openapi()


def render_schema() -> str:
    """Serialize deterministically (sorted keys, trailing newline) so diffs are stable."""
    return json.dumps(openapi_schema(), indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the schema to the path given as the first argument."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m gatp.api.export_openapi <output.json>", file=sys.stderr)
        return 2
    out = Path(args[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_schema(), encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
