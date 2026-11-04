"""In-process event bus feeding the UI's Server-Sent Events stream (per project)."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any


class EventBus:
    """Publish from any thread; subscribers are asyncio queues on the server's loop."""

    def __init__(self) -> None:
        self._subscribers: dict[int, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish(self, project_id: int, kind: str, data: dict[str, Any] | None = None) -> None:
        event = {"type": kind, "project_id": project_id, "data": data or {}}
        loop = self._loop
        if loop is None:
            return
        for queue in list(self._subscribers.get(project_id, ())):
            loop.call_soon_threadsafe(queue.put_nowait, event)

    async def stream(self, project_id: int, heartbeat_s: float = 15.0) -> AsyncGenerator[str]:
        """SSE-formatted events for one project until the client disconnects."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[project_id].add(queue)
        try:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=heartbeat_s)
                except TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
        finally:
            self._subscribers[project_id].discard(queue)
