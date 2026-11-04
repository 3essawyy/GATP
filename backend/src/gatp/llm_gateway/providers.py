"""Model providers behind one interface (ADR-003, ADR-016).

Each provider turns a ``ProviderRequest`` (system text, user text, JSON schema) into a
``ProviderResponse`` (raw text + token usage). Providers do not validate, cache or log: that
is the gateway's job. They talk plain HTTP via ``httpx`` so every request is easy to inspect.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx


class ProviderError(RuntimeError):
    """A provider call failed. ``retryable`` marks transient errors worth a backoff retry."""

    status = "error"

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class RateLimitedError(ProviderError):
    """HTTP 429 / quota exhausted."""

    status = "rate_limited"

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=True)


class ProviderUnavailableError(ProviderError):
    """Provider not configured or not reachable (no key, Ollama not running)."""

    status = "unavailable"


@dataclass(frozen=True)
class ProviderRequest:
    system: str
    user: str
    json_schema: dict[str, Any]
    temperature: float = 0.0


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    model: str
    model_version: str = ""
    input_tokens: int | None = None  # None = provider did not report
    output_tokens: int | None = None


class Provider(Protocol):
    """Anything that can answer a ``ProviderRequest``."""

    name: str
    model: str

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


def _raise_for_status(resp: httpx.Response, provider: str) -> None:
    if resp.status_code == 429:
        raise RateLimitedError(f"{provider}: rate limited (HTTP 429)")
    if resp.status_code >= 500:
        raise ProviderError(f"{provider}: server error HTTP {resp.status_code}", retryable=True)
    if resp.status_code >= 400:
        raise ProviderError(f"{provider}: HTTP {resp.status_code}: {resp.text[:300]}")


class GeminiProvider:
    """Google Gemini via the Generative Language REST API (free tier)."""

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_s: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=timeout_s)

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.api_key:
            raise ProviderUnavailableError("gemini: GATP_GEMINI_API_KEY is not set")
        body = {
            "systemInstruction": {"parts": [{"text": request.system}]},
            "contents": [{"role": "user", "parts": [{"text": request.user}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "responseMimeType": "application/json",
                "responseJsonSchema": request.json_schema,
            },
        }
        try:
            resp = self.client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                headers={"x-goog-api-key": self.api_key},
                json=body,
            )
        except httpx.TransportError as exc:
            raise ProviderError(f"gemini: {exc}", retryable=True) from exc
        _raise_for_status(resp, "gemini")
        data = resp.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError) as exc:
            reason = data.get("promptFeedback") or data.get("candidates", [{}])[0].get(
                "finishReason", "no content"
            )
            raise ProviderError(f"gemini: empty response ({reason})") from exc
        usage = data.get("usageMetadata", {})
        return ProviderResponse(
            text=text,
            model=self.model,
            model_version=str(data.get("modelVersion", "")),
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
        )

    def list_models(self) -> list[str]:
        """Model IDs this key can call with generateContent (used by ``poe llm-check``)."""
        if not self.api_key:
            raise ProviderUnavailableError("gemini: GATP_GEMINI_API_KEY is not set")
        resp = self.client.get(f"{self.base_url}/models", headers={"x-goog-api-key": self.api_key})
        _raise_for_status(resp, "gemini")
        return sorted(
            m["name"].removeprefix("models/")
            for m in resp.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        )


class OllamaProvider:
    """Local model through Ollama's chat API with a JSON-schema ``format``."""

    name = "ollama"

    def __init__(
        self,
        host: str,
        model: str,
        timeout_s: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.client = client or httpx.Client(timeout=timeout_s)

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        body = {
            "model": self.model,
            "stream": False,
            "format": request.json_schema,
            "options": {"temperature": request.temperature},
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
        }
        try:
            resp = self.client.post(f"{self.host}/api/chat", json=body)
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"ollama: not reachable at {self.host}") from exc
        except httpx.TransportError as exc:
            raise ProviderError(f"ollama: {exc}", retryable=True) from exc
        if resp.status_code == 404:
            raise ProviderUnavailableError(
                f"ollama: model {self.model!r} not found (run: ollama pull {self.model})"
            )
        _raise_for_status(resp, "ollama")
        data = resp.json()
        return ProviderResponse(
            text=data.get("message", {}).get("content", ""),
            model=self.model,
            model_version=str(data.get("model", "")),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
        )


Responder = Callable[[ProviderRequest], str | Exception]


@dataclass
class FakeProvider:
    """Deterministic provider for tests, CI and offline demos (always labelled ``fake``).

    ``script`` is consumed in order: each item is either response text or an exception to
    raise. When the script is empty, ``default`` decides the answer (text, or a callable).
    """

    name: str = "fake"
    model: str = "fake-model"
    script: list[str | Exception] = field(default_factory=list)
    default: str | Responder = "{}"
    latency_s: float = 0.0
    requests: list[ProviderRequest] = field(default_factory=list)

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.latency_s:
            time.sleep(self.latency_s)
        item: str | Exception
        if self.script:
            item = self.script.pop(0)
        elif callable(self.default):
            item = self.default(request)
        else:
            item = self.default
        if isinstance(item, Exception):
            raise item
        return ProviderResponse(text=item, model=self.model, model_version="fake-1")


def schema_example(schema: dict[str, Any]) -> str:
    """A tiny JSON string satisfying common schemas (used by the offline ``fake`` primary)."""
    return json.dumps(_example(schema, schema.get("$defs", {})))


def _example(schema: dict[str, Any], defs: dict[str, Any]) -> Any:
    if "$ref" in schema:
        return _example(defs[schema["$ref"].split("/")[-1]], defs)
    if "anyOf" in schema:
        return _example(schema["anyOf"][0], defs)
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object":
        props = schema.get("properties", {})
        return {k: _example(v, defs) for k, v in props.items() if k in schema.get("required", [])}
    if kind == "array":
        return []
    if kind == "integer":
        return 0
    if kind == "number":
        return 0.0
    if kind == "boolean":
        return False
    if kind == "null":
        return None
    return "example"
