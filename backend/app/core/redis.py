"""Redis client management - avoids circular import with main.py."""

import redis.asyncio as aioredis

# Global Redis client, set during app startup
_redis_client: aioredis.Redis | None = None


async def init_redis(url: str) -> aioredis.Redis | None:
    """Initialize Redis connection. Returns client or None if unavailable."""
    global _redis_client
    try:
        _redis_client = aioredis.from_url(url, decode_responses=True)
        await _redis_client.ping()
        return _redis_client
    except Exception as e:
        print(f"⚠️ Redis not available ({e}), using in-memory fallback")
        _redis_client = None
        return None


async def close_redis():
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


def get_redis() -> aioredis.Redis | None:
    """Get the global Redis client."""
    return _redis_client
