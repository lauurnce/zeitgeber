"""Request body size limit and a per-client rate limit, both in memory only.

The rate limiter keeps, per client, the times of its recent requests for one minute and
nothing else. The client key is a salted hash of the forwarded address; the address itself is
never stored or logged. Limits are per function instance: a burst spread over several
instances can exceed them, which is acceptable for a free, stateless planner (D41).
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from collections import deque
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class BodyTooLargeError(Exception):
    pass


class BodySizeLimit:
    """Rejects bodies over ``max_bytes`` with 413, by header and while streaming."""

    def __init__(self, app: ASGIApp, max_bytes: int, on_reject: ASGIApp) -> None:
        self.app, self.max_bytes, self.on_reject = app, max_bytes, on_reject

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        length = headers.get(b"content-length")
        if length is not None and (not length.isdigit() or int(length) > self.max_bytes):
            await self.on_reject(scope, receive, send)
            return
        seen = 0

        async def limited() -> Message:
            nonlocal seen
            message = await receive()
            if message["type"] == "http.request":
                seen += len(message.get("body", b""))
                if seen > self.max_bytes:
                    raise BodyTooLargeError
            return message

        try:
            await self.app(scope, limited, send)
        except BodyTooLargeError:
            await self.on_reject(scope, receive, send)


class RateLimiter:
    """Sliding one-minute window per client key."""

    def __init__(self, per_minute: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.per_minute = per_minute
        self.clock = clock
        self._salt = secrets.token_bytes(16)
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def key(self, forwarded_for: str | None, peer: str | None) -> str:
        address = (forwarded_for or "").split(",")[0].strip() or peer or "unknown"
        return hashlib.blake2b(address.encode(), key=self._salt, digest_size=12).hexdigest()

    def check(self, key: str) -> float | None:
        """None when the request may go ahead, otherwise seconds until it may."""
        now = self.clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= 60.0:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return 60.0 - (now - hits[0])
            hits.append(now)
            if len(self._hits) > 10_000:  # drop idle clients so memory stays bounded
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] >= 60.0]:
                    del self._hits[k]
            return None
