"""
mem0 Memory Service for Positivity Push
Manages personalized user context and conversation memory using the new MemoryClient.
"""

import logging
from typing import Dict, Any, List, Optional
from mem0 import MemoryClient

from app.config import settings

logger = logging.getLogger(__name__)

class Mem0Service:
    """Service class for mem0 memory management using MemoryClient"""
    
    def __init__(self):
        if not settings.MEM0_API_KEY or settings.MEM0_API_KEY == "your-mem0-api-key":
            logger.warning("mem0 API key not configured - memory features disabled")
            self.client = None
        else:
            try:
                self.client = MemoryClient(api_key=settings.MEM0_API_KEY)
                logger.info("mem0 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize mem0 client: {e}")
                self.client = None
    
    async def add_memory(
        self, 
        messages: List[Dict[str, str]], 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add conversation messages to memory for a user"""
        if not self.client:
            logger.warning("mem0 client not available - skipping memory add")
            return False
            
        try:
            # Use the correct mem0 API format - user_id is REQUIRED
            result = self.client.add(
                messages, 
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Check if memories were successfully added
            success = False
            if isinstance(result, dict) and 'results' in result:
                success = len(result['results']) > 0
                logger.info(f"Memory added for user {user_id}: {len(result['results'])} memories created")
            else:
                logger.warning(f"Unexpected mem0 response format: {result}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add memory for user {user_id}: {e}")
            return False
    
    async def get_memories(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relevant memories for a user"""
        if not self.client:
            logger.warning("mem0 client not available - returning empty memories")
            return []
            
        try:
            if query:
                # Search for specific memories - returns a list directly
                result = self.client.search(query, user_id=user_id)
            else:
                # Get all memories for user - returns a list directly
                result = self.client.get_all(user_id=user_id)
            
            # The result is already a list of memory objects
            if isinstance(result, list):
                memories = result
            else:
                logger.warning(f"Unexpected mem0 response format: {result}")
                memories = []
            
            logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get memories for user {user_id}: {e}")
            return []
    
    async def add_conversation(self, user_id: str, user_message: str, assistant_response: str) -> bool:
        """Add a conversation exchange to memory"""
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ]
        return await self.add_memory(messages, user_id)
    
    async def get_user_context(self, user_id: str) -> str:
        """Get formatted user context for AI prompts"""
        memories = await self.get_memories(user_id)
        
        if not memories:
            return "No previous context available."
        
        # Format memories for AI context
        context_parts = []
        for memory in memories[-10:]:  # Last 10 memories
            if isinstance(memory, dict):
                # mem0 stores the actual memory text in 'memory' field
                content = memory.get('memory', memory.get('content', memory.get('text', str(memory))))
                context_parts.append(f"- {content}")
        
        return "Previous context:\n" + "\n".join(context_parts)
    
    def is_available(self) -> bool:
        """Check if mem0 service is available"""
        return self.client is not None
