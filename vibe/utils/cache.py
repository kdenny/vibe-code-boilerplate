"""File-based cache with TTL for API responses."""

import json
import os
import time
from pathlib import Path
from typing import Any

CACHE_DIR = Path(".vibe/cache")
DEFAULT_TTL = 3600  # 1 hour


class Cache:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or CACHE_DIR

    def get(self, key: str) -> Any | None:
        """Get a cached value by key. Returns None if missing or expired."""
        if os.environ.get("VIBE_NO_CACHE") == "1":
            return None

        cache_file = self._cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())
            if time.time() > data.get("expires_at", 0):
                cache_file.unlink(missing_ok=True)
                return None
            return data.get("value")
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Cache a value with a TTL in seconds."""
        if os.environ.get("VIBE_NO_CACHE") == "1":
            return

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_dir / f"{key}.json"

        try:
            cache_file.write_text(
                json.dumps(
                    {
                        "value": value,
                        "expires_at": time.time() + ttl,
                        "cached_at": time.time(),
                    }
                )
            )
        except OSError:
            pass  # Silently fail if we can't write cache

    def invalidate(self, key: str | None = None) -> int:
        """Invalidate a specific key or all keys. Returns count of removed entries."""
        if not self._cache_dir.exists():
            return 0

        count = 0
        if key:
            cache_file = self._cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                count = 1
        else:
            for f in self._cache_dir.glob("*.json"):
                f.unlink()
                count += 1
        return count

    def status(self) -> list[dict[str, Any]]:
        """Get status of all cached entries."""
        if not self._cache_dir.exists():
            return []

        entries = []
        now = time.time()
        for f in sorted(self._cache_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                cached_at = data.get("cached_at", 0)
                expires_at = data.get("expires_at", 0)
                age_seconds = int(now - cached_at)
                remaining = int(expires_at - now)
                entries.append(
                    {
                        "key": f.stem,
                        "age_seconds": age_seconds,
                        "remaining_seconds": max(0, remaining),
                        "expired": now > expires_at,
                    }
                )
            except (json.JSONDecodeError, OSError):
                entries.append({"key": f.stem, "error": "invalid"})
        return entries


# Module-level cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the shared cache instance."""
    return _cache
