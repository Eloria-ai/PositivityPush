"""
mem0 Memory Service for Positivity Push
Manages personalized user context and conversation memory using the new MemoryClient.
"""

from typing import Dict, Any, List, Optional
from mem0 import MemoryClient

from app.config import settings
from app.logging_config import get_logger

# Configure structured logging
logger = get_logger("app.services.mem0")

class Mem0Service:
    """Service class for mem0 memory management using MemoryClient"""
    
    def __init__(self):
        if not settings.MEM0_API_KEY or settings.MEM0_API_KEY == "your-mem0-api-key":
            logger.warning("mem0_api_key_not_configured",
                          message="memory features disabled")
            self.client = None
        else:
            try:
                self.client = MemoryClient(api_key=settings.MEM0_API_KEY)
                logger.info("mem0_client_initialized")
            except Exception as e:
                logger.error("mem0_client_initialization_failed",
                            error=str(e),
                            exc_info=True)
                self.client = None
    
    async def add_memory(
        self, 
        messages: List[Dict[str, str]], 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add conversation messages to memory for a user"""
        if not self.client:
            logger.warning("mem0_client_unavailable",
                          operation="add_memory",
                          user_id=user_id)
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
                logger.info("mem0_memory_added",
                           user_id=user_id,
                           memories_created=len(result['results']))
            else:
                logger.warning("mem0_unexpected_response_format",
                              user_id=user_id,
                              response_format=str(type(result)))
            
            return success
            
        except Exception as e:
            logger.error("mem0_add_memory_failed",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
            return False
    
    async def get_memories(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relevant memories for a user"""
        if not self.client:
            logger.warning("mem0_client_unavailable",
                          operation="get_memories",
                          user_id=user_id)
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
                logger.warning("mem0_unexpected_response_format",
                              user_id=user_id,
                              operation="get_memories", 
                              response_format=str(type(result)))
                memories = []
            
            logger.info("mem0_memories_retrieved",
                       user_id=user_id,
                       memory_count=len(memories))
            return memories
            
        except Exception as e:
            logger.error("mem0_get_memories_failed",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
