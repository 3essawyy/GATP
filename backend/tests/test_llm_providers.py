"""TC-105: provider wire formats (Gemini REST, Ollama chat) against mocked HTTP."""

import json
from typing import Any

import httpx
import pytest

from gatp.llm_gateway.providers import (
    GeminiProvider,
    OllamaProvider,
    ProviderError,
    ProviderRequest,
    ProviderUnavailableError,
    RateLimitedError,
)

REQ = ProviderRequest(system="sys", user="usr", json_schema={"type": "object"})


def client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler)


def test_gemini_request_and_usage() -> None:
    seen: dict[str, Any] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers["x-goog-api-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}],
                "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 3},
                "modelVersion": "gemini-2.5-flash-001",
            },
        )

    p = GeminiProvider("secret", "gemini-2.5-flash", client=client(httpx.MockTransport(handle)))
    r = p.generate(REQ)
    assert seen["url"].endswith("/models/gemini-2.5-flash:generateContent")
    assert seen["key"] == "secret"
    body = seen["body"]
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["responseJsonSchema"] == {"type": "object"}
    assert body["systemInstruction"]["parts"][0]["text"] == "sys"
    assert (r.text, r.input_tokens, r.output_tokens, r.model_version) == (
        '{"ok": true}',
        12,
        3,
        "gemini-2.5-flash-001",
    )


def test_gemini_errors() -> None:
    with pytest.raises(ProviderUnavailableError):
        GeminiProvider("", "m").generate(REQ)
    for status, exc in ((429, RateLimitedError), (503, ProviderError), (400, ProviderError)):
        p = GeminiProvider(
            "k", "m", client=client(httpx.MockTransport(lambda _r, s=status: httpx.Response(s)))
        )
        with pytest.raises(exc) as info:
            p.generate(REQ)
        assert info.value.retryable == (status != 400)


def test_gemini_empty_candidates_is_an_error() -> None:
    p = GeminiProvider(
        "k",
        "m",
        client=client(
            httpx.MockTransport(
                lambda _r: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})
            )
        ),
    )
    with pytest.raises(ProviderError, match="empty response"):
        p.generate(REQ)


def test_gemini_list_models() -> None:
    payload = {
        "models": [
            {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/embedding-001", "supportedGenerationMethods": ["embedContent"]},
        ]
    }
    p = GeminiProvider(
        "k", "m", client=client(httpx.MockTransport(lambda _r: httpx.Response(200, json=payload)))
    )
    assert p.list_models() == ["gemini-2.5-flash"]


def test_ollama_request_and_usage() -> None:
    seen: dict[str, Any] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "qwen2.5-coder:3b",
                "message": {"content": '{"ok": true}'},
                "prompt_eval_count": 20,
                "eval_count": 5,
            },
        )

    transport = client(httpx.MockTransport(handle))
    p = OllamaProvider("http://ollama:11434", "qwen2.5-coder:3b", client=transport)
    r = p.generate(REQ)
    body = seen["body"]
    assert body["format"] == {"type": "object"}
    assert body["stream"] is False
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert (r.input_tokens, r.output_tokens) == (20, 5)


def test_ollama_unreachable_or_missing_model() -> None:
    def refuse(_r: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ProviderUnavailableError, match="not reachable"):
        OllamaProvider("http://x", "m", client=client(httpx.MockTransport(refuse))).generate(REQ)
    missing = OllamaProvider(
        "http://x", "m", client=client(httpx.MockTransport(lambda _r: httpx.Response(404)))
    )
    with pytest.raises(ProviderUnavailableError, match="ollama pull m"):
        missing.generate(REQ)
