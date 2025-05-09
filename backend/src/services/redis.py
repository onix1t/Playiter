import json
import redis
from typing import List

from ..config import settings

class RedisService:
    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL)

    def cache_data(self, key: str, value: dict, ttl: int = 3600) -> bool:
        try:
            serialized = json.dumps(value)
            return self.client.setex(key, ttl, serialized)
        except Exception:
            return False

    def get_cached_data(self, key: str) -> dict:
        try:
            data = self.client.get(key)
            return json.loads(data.decode()) if data else None
        except Exception:
            return None

    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        try:
            return self.client.keys(pattern)
        except Exception:
            return []

redis_service = RedisService()