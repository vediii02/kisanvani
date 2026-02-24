from typing import Dict, Optional
import uuid
from datetime import datetime, timezone
import redis.asyncio as redis
from core.config import settings

class SessionManager:
    def __init__(self):
        self.redis_client = None
    
    async def connect(self):
        self.redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
    
    def generate_session_id(self) -> str:
        return f"session_{uuid.uuid4()}"
    
    async def create_session(self, phone_number: str, metadata: Dict = None) -> str:
        session_id = self.generate_session_id()
        session_data = {
            'phone_number': phone_number,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'active',
            **(metadata or {})
        }
        
        await self.redis_client.hset(f"session:{session_id}", mapping=session_data)
        await self.redis_client.expire(f"session:{session_id}", 3600)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        data = await self.redis_client.hgetall(f"session:{session_id}")
        return data if data else None
    
    async def update_session(self, session_id: str, updates: Dict):
        await self.redis_client.hset(f"session:{session_id}", mapping=updates)
    
    async def end_session(self, session_id: str):
        await self.redis_client.hset(f"session:{session_id}", 'status', 'ended')
        await self.redis_client.hset(f"session:{session_id}", 'end_time', datetime.now(timezone.utc).isoformat())

session_manager = SessionManager()