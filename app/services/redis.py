import redis
from app.config import settings
import json

class RedisService:
    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL)

    def cache_data(self, key: str, value: dict, ttl: int = 3600) -> bool:
        try:
            serialized = json.dumps(value)
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False

    def get_cached_data(self, key: str) -> dict:
        try:
            data = self.client.get(key)
            return json.loads(data.decode()) if data else None
        except Exception as e:
            print(f"Redis get cache error: {e}")
            return None

# Глобальный экземпляр
redis_service = RedisService()