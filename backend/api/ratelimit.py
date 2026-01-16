from .redis import RedisClient
import time

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        
    async def get_redis(self):
        return RedisClient.get_instance()

    async def is_allowed(self, key: str) -> bool:
        """
        Check if the request is allowed for the given key.
        Uses a fixed window algorithm.
        """
        redis = await self.get_redis()
        current_window = int(time.time() / self.window_seconds)
        redis_key = f"rate_limit:{key}:{current_window}"
        
        # Increment and get new value
        count = await redis.incr(redis_key)
        
        # If it's the first request in this window, set expiration
        if count == 1:
            await redis.expire(redis_key, self.window_seconds + 5)
            
        return count <= self.limit
    
    async def get_remaining(self, key: str) -> int:
        redis = await self.get_redis()
        current_window = int(time.time() / self.window_seconds)
        redis_key = f"rate_limit:{key}:{current_window}"
        count = await redis.get(redis_key)
        if count is None:
            return self.limit
        return max(0, self.limit - int(count))
