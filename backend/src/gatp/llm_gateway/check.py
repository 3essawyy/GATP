"""``uv run poe llm-check``: verify model configuration with one tiny, logged call.

Prints the configured providers, lists the Gemini models the key can use (if a key is set),
then sends the ``ping`` template through the real gateway so the call appears in the usage log.
"""

from __future__ import annotations

from pydantic import BaseModel

from gatp.config import get_settings
from gatp.llm_gateway.gateway import LLMError, LLMGateway
from gatp.llm_gateway.providers import GeminiProvider, ProviderError
from gatp.store.db import Database


class Ping(BaseModel):
    ok: bool
    echo: str


def main() -> int:
    """Run the check; exit code 0 only if a provider answered with valid JSON."""
    settings = get_settings()
    print(f"primary={settings.llm_primary} fallback={settings.llm_fallback or '-'}")
    key_state = "set" if settings.gemini_api_key else "MISSING"
    print(f"gemini model={settings.gemini_model} key={key_state}")
    print(f"ollama host={settings.ollama_host} model={settings.ollama_model}")
    if settings.gemini_api_key:
        try:
            models = GeminiProvider(settings.gemini_api_key, settings.gemini_model).list_models()
            flash = [m for m in models if "flash" in m]
            print(f"gemini models with generateContent ({len(models)}): {', '.join(flash)}")
            if settings.gemini_model not in models:
                print(f"WARNING: {settings.gemini_model} is not in the list for this key")
        except ProviderError as exc:
            print(f"gemini model list failed: {exc}")
    db = Database.from_settings(settings)
    db.migrate()
    gateway = LLMGateway.from_settings(settings, db)
    gateway.cache = False  # always a fresh call
    try:
        result = gateway.complete_structured("ping", {"word": "gatp"}, Ping)
    except LLMError as exc:
        print(f"FAILED: {exc}")
        for c in exc.calls:
            print(f"  {c.provider}/{c.model}: {c.status} {c.error}")
        return 1
    c = result.call
    tokens = f"{c.input_tokens} in / {c.output_tokens} out" + (
        " (estimated)" if c.tokens_estimated else ""
    )
    print(f"OK via {c.provider} model={c.model} version={c.model_version or '?'}")
    print(f"   tokens {tokens}, latency {c.latency_ms} ms, answer={result.value.model_dump()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
