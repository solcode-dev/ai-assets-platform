import json
from typing import AsyncGenerator
from redis.asyncio import Redis, from_url
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """Redis Pub/Sub을 활용한 비동기 이벤트 버스"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Redis = None

    async def connect(self):
        if not self._redis:
            self._redis = from_url(self.redis_url, decode_responses=True)

    async def publish(self, channel: str, message: dict):
        if not self._redis:
            await self.connect()
        try:
            await self._redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish message to {channel}: {e}")

    def publish_sync(self, channel: str, message: dict):
        """이벤트를 동기식으로 발행합니다 (비상용)."""
        import redis
        try:
            r = redis.from_url(self.redis_url)
            r.publish(channel, json.dumps(message))
            r.close()
        except Exception as e:
            logger.error(f"Failed to publish (sync) message to {channel}: {e}")

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """특정 채널의 이벤트를 구독하여 스트리밍합니다."""
        if not self._redis:
            await self.connect()
        
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        yield message["data"]
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None

# 싱글톤 인스턴스
event_bus = EventBus(settings.REDIS_URL)
