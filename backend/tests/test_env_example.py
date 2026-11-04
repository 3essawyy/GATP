"""T-011: `.env.example` documents every setting (REQ-P1-S: model config without secrets)."""

from pathlib import Path

from gatp.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_every_setting_is_documented() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    missing = [
        f"GATP_{name.upper()}"
        for name in Settings.model_fields
        if f"GATP_{name.upper()}" not in text
    ]
    assert missing == [], f"add to .env.example: {missing}"


def test_example_contains_no_secret_values() -> None:
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith("GATP_GEMINI_API_KEY="):
            assert line == "GATP_GEMINI_API_KEY="
