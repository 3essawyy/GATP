"""The OpenAPI export feeds the generated TS client; it must be complete and deterministic."""

import json
from pathlib import Path

from gatp.api import export_openapi

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_schema_contains_health_operation() -> None:
    schema = export_openapi.openapi_schema()
    op = schema["paths"]["/api/health"]["get"]
    assert op["operationId"] == "getHealth"
    assert "Health" in schema["components"]["schemas"]


def test_render_is_deterministic() -> None:
    assert export_openapi.render_schema() == export_openapi.render_schema()


def test_main_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "openapi.json"
    assert export_openapi.main([str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["info"]["title"] == "GATP API"


def test_main_rejects_missing_argument() -> None:
    assert export_openapi.main([]) == 2


def test_committed_schema_is_current() -> None:
    """Fails if someone changed the API without running `uv run poe gen-client`."""
    committed = (REPO_ROOT / "frontend" / "openapi.json").read_text(encoding="utf-8")
    assert committed == export_openapi.render_schema(), "run: uv run poe gen-client"
