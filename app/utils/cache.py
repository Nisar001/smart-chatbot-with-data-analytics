import asyncio
import time
from typing import Any


class TTLCache:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str):
        async with self._lock:
            value = self._store.get(key)
            if not value:
                return None
            expires_at, payload = value
            if expires_at < time.time():
                self._store.pop(key, None)
                return None
            return payload

    async def set(self, key: str, payload: Any, ttl_seconds: int):
        async with self._lock:
            self._store[key] = (time.time() + ttl_seconds, payload)
