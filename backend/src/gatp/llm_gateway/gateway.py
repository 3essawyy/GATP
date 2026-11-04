"""The single entry point for model calls (ADR-003, ADR-016).

``LLMGateway.complete_structured`` renders a versioned template, asks providers in order
(primary, then fallback), validates the JSON answer against a Pydantic schema (plus an
optional semantic ``check``), retries once with the validation error ("repair retry"),
backs off on rate limits, serves identical requests from the cache (marked ``reused``) and
logs **every attempt** to the ``llm_calls`` table.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from gatp.config import Settings
from gatp.llm_gateway.providers import (
    FakeProvider,
    GeminiProvider,
    OllamaProvider,
    Provider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
    ProviderUnavailableError,
    schema_example,
)
from gatp.llm_gateway.templates import TemplateRegistry, registry
from gatp.store.db import Database
from gatp.store.llm_calls import LlmCallDTO, LlmCallIn, LlmCallRepository

Check = Callable[[Any], list[str]]


class LLMError(RuntimeError):
    """Base class; ``calls`` holds every logged attempt for the failed request."""

    def __init__(self, message: str, calls: Sequence[LlmCallDTO]) -> None:
        super().__init__(message)
        self.calls = tuple(calls)


class LLMOutputError(LLMError):
    """Every provider answered, but no answer passed schema/semantic validation."""


class LLMUnavailableError(LLMError):
    """No provider could answer (missing key, offline, rate limits exhausted)."""


@dataclass(frozen=True)
class LLMResult[T: BaseModel]:
    """A validated answer plus the usage rows logged while producing it."""

    value: T
    call: LlmCallDTO
    attempts: tuple[LlmCallDTO, ...]

    @property
    def reused(self) -> bool:
        return self.call.cache == "reused"


def estimate_tokens(text: str) -> int:
    """Rough estimate (~4 characters per token). Rows using it are flagged ``estimated``."""
    return max(1, math.ceil(len(text) / 4))


def request_hash(template_id: str, version: int, system: str, user: str, schema: Any) -> str:
    """Provider-independent identity of a request, used as the cache key."""
    payload = json.dumps(
        {"t": template_id, "v": version, "s": system, "u": user, "schema": schema},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LLMGateway:
    """Provider-agnostic, logged, validated structured completion."""

    def __init__(
        self,
        providers: Sequence[Provider],
        calls: LlmCallRepository,
        *,
        cache: bool = True,
        max_retries: int = 2,
        backoff_s: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
        templates: TemplateRegistry = registry,
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self.providers = list(providers)
        self.calls = calls
        self.cache = cache
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self.sleep = sleep
        self.templates = templates

    @classmethod
    def from_settings(cls, settings: Settings, db: Database) -> LLMGateway:
        """Build primary (+ optional fallback) providers from ``GATP_LLM_*`` settings."""
        names = [settings.llm_primary]
        if settings.llm_fallback and settings.llm_fallback != settings.llm_primary:
            names.append(settings.llm_fallback)
        return cls(
            [make_provider(n, settings) for n in names],
            LlmCallRepository(db),
            cache=settings.llm_cache,
            max_retries=settings.llm_max_retries,
            backoff_s=settings.llm_backoff_s,
        )

    def complete_structured[T: BaseModel](
        self,
        template_id: str,
        inputs: dict[str, Any],
        schema: type[T],
        *,
        page_data: Any = None,
        project_id: int | None = None,
        check: Check | None = None,
    ) -> LLMResult[T]:
        """Return a validated ``schema`` instance or raise an ``LLMError`` subclass."""
        template = self.templates.get(template_id)
        system, user = template.render(inputs, page_data)
        json_schema = schema.model_json_schema()
        key = request_hash(template.id, template.version, system, user, json_schema)
        logged: list[LlmCallDTO] = []

        def log(**fields: Any) -> LlmCallDTO:
            row = self.calls.record(
                LlmCallIn(
                    purpose=template.id,
                    template_version=template.version,
                    request_hash=key,
                    project_id=project_id,
                    **fields,
                )
            )
            logged.append(row)
            return row

        if self.cache:
            hit = self.calls.find_fresh_success(key)
            if hit is not None:
                started = time.perf_counter()
                value, errors = _validate(hit.response, schema, check)
                if value is not None and not errors:
                    row = log(
                        provider=hit.provider,
                        model=hit.model,
                        model_version=hit.model_version,
                        input_tokens=hit.input_tokens,
                        output_tokens=hit.output_tokens,
                        tokens_estimated=hit.tokens_estimated,
                        latency_ms=_ms(started),
                        cache="reused",
                        response=hit.response,
                    )
                    return LLMResult(value, row, tuple(logged))

        output_errors: list[str] = []
        unavailable: list[str] = []
        for provider in self.providers:
            request = ProviderRequest(system=system, user=user, json_schema=json_schema)
            for repair in (False, True):
                response, latency_ms, error = self._call_with_retries(provider, request, log)
                if response is None:
                    unavailable.append(error)
                    break
                value, errors = _validate(response.text, schema, check)
                usage = _usage(provider.name, response, request, latency_ms)
                if value is not None and not errors:
                    row = log(**usage, status="ok", response=response.text)
                    return LLMResult(value, row, tuple(logged))
                problem = "; ".join(errors)[:2000]
                log(**usage, status="invalid_output", error=problem, response=response.text)
                output_errors.append(f"{provider.name}: {problem}")
                if repair:
                    break
                request = ProviderRequest(
                    system=system,
                    user=(
                        f"{user}\n\nYour previous answer was rejected: {problem}\n"
                        "Return only JSON that matches the schema and uses only given ids."
                    ),
                    json_schema=json_schema,
                )
        if output_errors:
            raise LLMOutputError(
                "model output failed validation: " + " | ".join(output_errors), logged
            )
        raise LLMUnavailableError("no model provider available: " + " | ".join(unavailable), logged)

    def _call_with_retries(
        self,
        provider: Provider,
        request: ProviderRequest,
        log: Callable[..., LlmCallDTO],
    ) -> tuple[ProviderResponse | None, int, str]:
        """Call one provider with exponential backoff on retryable errors; log failures."""
        delay = self.backoff_s
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                response = provider.generate(request)
            except ProviderError as exc:
                log(
                    provider=provider.name,
                    model=provider.model,
                    latency_ms=_ms(started),
                    status=exc.status,
                    error=str(exc)[:2000],
                )
                if isinstance(exc, ProviderUnavailableError) or not exc.retryable:
                    return None, 0, str(exc)
                if attempt == self.max_retries:
                    return None, 0, f"{exc} (after {attempt + 1} attempts)"
                self.sleep(delay)
                delay *= 2
                continue
            return response, _ms(started), ""
        return None, 0, "unreachable"  # pragma: no cover


def _usage(
    provider: str, response: ProviderResponse, request: ProviderRequest, latency_ms: int
) -> dict[str, Any]:
    estimated = response.input_tokens is None or response.output_tokens is None
    return {
        "provider": provider,
        "model": response.model,
        "model_version": response.model_version,
        "input_tokens": response.input_tokens
        if response.input_tokens is not None
        else estimate_tokens(request.system + request.user),
        "output_tokens": response.output_tokens
        if response.output_tokens is not None
        else estimate_tokens(response.text),
        "tokens_estimated": estimated,
        "latency_ms": latency_ms,
    }


def _validate[T: BaseModel](
    text: str, schema: type[T], check: Check | None
) -> tuple[T | None, list[str]]:
    try:
        value = schema.model_validate_json(text)
    except ValidationError as exc:
        return None, [f"{'.'.join(map(str, e['loc'])) or 'root'}: {e['msg']}" for e in exc.errors()]
    return value, (check(value) if check else [])


def _ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def make_provider(name: str, settings: Settings) -> Provider:
    """Instantiate a provider by name from settings."""
    if name == "gemini":
        return GeminiProvider(
            settings.gemini_api_key,
            settings.gemini_model,
            settings.gemini_base_url,
            settings.llm_timeout_s,
        )
    if name == "ollama":
        return OllamaProvider(settings.ollama_host, settings.ollama_model, settings.llm_timeout_s)
    if name == "fake":
        return FakeProvider(default=lambda req: schema_example(req.json_schema))
    raise ValueError(f"unknown LLM provider {name!r}; expected gemini | ollama | fake")
