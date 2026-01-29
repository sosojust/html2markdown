
import pytest
from unittest.mock import AsyncMock
from backend.api.ratelimit import RateLimiter
from backend.api.redis import RedisClient

@pytest.mark.asyncio
async def test_rate_limiter_allowed():
    # Mock Redis
    mock_redis = AsyncMock()
    # First call returns 1
    mock_redis.incr.return_value = 1
    
    # Patch get_instance
    original_get_instance = RedisClient.get_instance
    RedisClient.get_instance = lambda: mock_redis
    
    try:
        limiter = RateLimiter(limit=10, window_seconds=60)
        allowed = await limiter.is_allowed("test_key")
        assert allowed is True
        mock_redis.incr.assert_called()
        mock_redis.expire.assert_called()
        
    finally:
        RedisClient.get_instance = original_get_instance

@pytest.mark.asyncio
async def test_rate_limiter_blocked():
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 11 # > limit 10
    
    original_get_instance = RedisClient.get_instance
    RedisClient.get_instance = lambda: mock_redis
    
    try:
        limiter = RateLimiter(limit=10, window_seconds=60)
        allowed = await limiter.is_allowed("test_key")
        assert allowed is False
        
    finally:
        RedisClient.get_instance = original_get_instance
