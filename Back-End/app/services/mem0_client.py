"""
mem0 Memory Service for Positivity Push
Manages personalized user context and conversation memory.
"""

import httpx
import json
import logging
from typing import Dict, Any, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

class Mem0Service:
    """Service class for mem0 memory management"""
    
    def __init__(self):
        self.base_url = settings.MEM0_URL or "https://api.mem0.ai"
        self.headers = {
            "Authorization": f"Bearer {settings.MEM0_API_KEY}",
            "Content-Type": "application/json"
        }
    
    async def add_memory(
        self, 
        user_id: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add memory for user"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "user_id": user_id,
                    "message": message,
                    "metadata": metadata or {}
                }
                
                response = await client.post(
                    f"{self.base_url}/memories",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Memory added for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to add memory: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error adding memory to mem0: {e}")
            return False
    
    async def get_memories(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> str:
        """Get user memories as formatted string"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "user_id": user_id,
                    "limit": limit
                }
                
                response = await client.get(
                    f"{self.base_url}/memories",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    memories = response.json().get("memories", [])
                    
                    # Format memories into readable context
                    if memories:
                        memory_text = "\\n".join([
                            f"- {memory.get('message', '')}" 
                            for memory in memories
                        ])
                        logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
                        return memory_text
                    else:
                        return ""
                else:
                    logger.error(f"Failed to get memories: {response.text}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error getting memories from mem0: {e}")
            return ""
    
    async def search_memories(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search user memories with query"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "user_id": user_id,
                    "query": query,
                    "limit": limit
                }
                
                response = await client.post(
                    f"{self.base_url}/memories/search",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    logger.info(f"Found {len(results)} memories for query: {query}")
                    return results
                else:
                    logger.error(f"Failed to search memories: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def update_memory(
        self, 
        memory_id: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing memory"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": message,
                    "metadata": metadata or {}
                }
                
                response = await client.put(
                    f"{self.base_url}/memories/{memory_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Memory {memory_id} updated")
                    return True
                else:
                    logger.error(f"Failed to update memory: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    async def delete_user_memories(self, user_id: str) -> bool:
        """Delete all memories for a user (GDPR compliance)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/memories/users/{user_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"All memories deleted for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to delete user memories: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting user memories: {e}")
            return False