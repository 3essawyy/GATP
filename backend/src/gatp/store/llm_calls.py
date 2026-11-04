"""LLM call log repository (HLD §10): every model call, fresh or reused, is one row."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from gatp.store.db import Database
from gatp.store.models import LlmCall


@dataclass(frozen=True)
class LlmCallIn:
    """What the gateway records for one call attempt."""

    purpose: str
    template_version: int
    provider: str
    model: str
    request_hash: str
    model_version: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_estimated: bool = False
    latency_ms: int = 0
    cache: str = "fresh"  # fresh | reused
    status: str = "ok"  # ok | invalid_output | rate_limited | error | unavailable
    error: str = ""
    response: str = ""
    request: str = ""
    project_id: int | None = None


@dataclass(frozen=True)
class LlmCallDTO:
    id: int
    project_id: int | None
    purpose: str
    template_version: int
    provider: str
    model: str
    model_version: str
    request_hash: str
    input_tokens: int
    output_tokens: int
    tokens_estimated: bool
    latency_ms: int
    cache: str
    status: str
    error: str
    request: str
    response: str
    created_at: datetime


def _dto(c: LlmCall) -> LlmCallDTO:
    return LlmCallDTO(
        id=c.id,
        project_id=c.project_id,
        purpose=c.purpose,
        template_version=c.template_version,
        provider=c.provider,
        model=c.model,
        model_version=c.model_version,
        request_hash=c.request_hash,
        input_tokens=c.input_tokens,
        output_tokens=c.output_tokens,
        tokens_estimated=c.tokens_estimated,
        latency_ms=c.latency_ms,
        cache=c.cache,
        status=c.status,
        error=c.error,
        request=c.request,
        response=c.response,
        created_at=c.created_at,
    )


class LlmCallRepository:
    """Append-only usage log plus the lookup used for response caching."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, call: LlmCallIn) -> LlmCallDTO:
        with self.db.session() as s:
            row = LlmCall(
                project_id=call.project_id,
                purpose=call.purpose,
                template_version=call.template_version,
                provider=call.provider,
                model=call.model,
                model_version=call.model_version,
                request_hash=call.request_hash,
                input_tokens=call.input_tokens,
                output_tokens=call.output_tokens,
                tokens_estimated=call.tokens_estimated,
                latency_ms=call.latency_ms,
                cache=call.cache,
                status=call.status,
                error=call.error,
                request=call.request,
                response=call.response,
            )
            s.add(row)
            s.flush()
            return _dto(row)

    def find_fresh_success(self, request_hash: str) -> LlmCallDTO | None:
        """The most recent successful *fresh* call with this request hash (cache source)."""
        with self.db.session() as s:
            row = s.scalar(
                select(LlmCall)
                .where(
                    LlmCall.request_hash == request_hash,
                    LlmCall.status == "ok",
                    LlmCall.cache == "fresh",
                )
                .order_by(LlmCall.id.desc())
                .limit(1)
            )
            return None if row is None else _dto(row)

    def recent(self, project_id: int | None = None, limit: int = 200) -> list[LlmCallDTO]:
        """Newest first; all projects when ``project_id`` is None."""
        with self.db.session() as s:
            q = select(LlmCall)
            if project_id is not None:
                q = q.where(LlmCall.project_id == project_id)
            return [_dto(c) for c in s.scalars(q.order_by(LlmCall.id.desc()).limit(limit))]
