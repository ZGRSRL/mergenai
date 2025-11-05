#!/usr/bin/env python3
"""
Redis Cache Manager for LLM Proposal Generation
Maliyet optimizasyonu için LLM yanıtlarını cache'ler
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching disabled")

class RedisCacheManager:
    """LLM proposal yanıtlarını Redis'te cache'ler"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis cache manager
        
        Args:
            redis_url: Redis connection URL (default: from env or localhost)
        """
        self.redis_client = None
        self.connected = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not installed - caching disabled")
            return
        
        try:
            # Redis URL from env or default
            if not redis_url:
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            
            # Docker içinde 'redis' hostname, host makinede 'localhost'
            if 'redis://redis:' in redis_url:
                # Docker içinden çalışıyor
                pass
            elif 'redis://localhost:' not in redis_url and 'redis://' in redis_url:
                # Host makineden çalışıyor, localhost kullan
                redis_url = redis_url.replace('redis://redis:', 'redis://localhost:')
            
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info(f"✅ Redis connected: {redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e} - Caching disabled")
            self.connected = False
            self.redis_client = None
    
    def _generate_cache_key(self, query: str, notice_id: Optional[str] = None, 
                           hybrid_alpha: float = 0.7, topk: int = 20) -> str:
        """
        Generate cache key from query and parameters
        
        Args:
            query: User query
            notice_id: Optional notice ID
            hybrid_alpha: Hybrid search alpha
            topk: Top-K value
            
        Returns:
            Cache key string
        """
        # Create hash from all parameters
        key_data = f"{query}|{notice_id}|{hybrid_alpha}|{topk}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        
        # Cache key format: proposal:{hash}
        cache_key = f"proposal:{key_hash}"
        return cache_key
    
    def get(self, query: str, notice_id: Optional[str] = None,
            hybrid_alpha: float = 0.7, topk: int = 20) -> Optional[Dict[str, Any]]:
        """
        Get cached proposal response
        
        Args:
            query: User query
            notice_id: Optional notice ID
            hybrid_alpha: Hybrid search alpha
            topk: Top-K value
            
        Returns:
            Cached response dict or None
        """
        if not self.connected or not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(query, notice_id, hybrid_alpha, topk)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"💰 Cache HIT: {cache_key[:20]}...")
                return json.loads(cached_data)
            else:
                logger.info(f"❌ Cache MISS: {cache_key[:20]}...")
                return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(self, query: str, response: Dict[str, Any], 
            notice_id: Optional[str] = None, hybrid_alpha: float = 0.7,
            topk: int = 20, ttl: int = 3600) -> bool:
        """
        Cache proposal response
        
        Args:
            query: User query
            response: Response dict to cache
            notice_id: Optional notice ID
            hybrid_alpha: Hybrid search alpha
            topk: Top-K value
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully
        """
        if not self.connected or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(query, notice_id, hybrid_alpha, topk)
            
            # Add cache metadata
            cached_response = {
                **response,
                '_cache_metadata': {
                    'cached_at': datetime.now().isoformat(),
                    'cache_key': cache_key,
                    'ttl': ttl
                }
            }
            
            # Cache with TTL
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cached_response, ensure_ascii=False)
            )
            
            logger.info(f"💾 Cache SET: {cache_key[:20]}... (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics
        
        Returns:
            Stats dict with key count, memory usage, etc.
        """
        if not self.connected or not self.redis_client:
            return {
                'connected': False,
                'keys': 0,
                'memory_mb': 0.0,
                'error': 'Redis not connected'
            }
        
        try:
            # Get info
            info = self.redis_client.info('memory')
            
            # Count proposal keys
            proposal_keys = len(self.redis_client.keys('proposal:*'))
            
            # Memory usage in MB
            memory_bytes = info.get('used_memory', 0)
            memory_mb = memory_bytes / (1024 * 1024)
            
            return {
                'connected': True,
                'keys': proposal_keys,
                'memory_mb': round(memory_mb, 2),
                'total_keys': self.redis_client.dbsize()
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                'connected': False,
                'keys': 0,
                'memory_mb': 0.0,
                'error': str(e)
            }
    
    def clear_cache(self) -> bool:
        """
        Clear all proposal cache keys
        
        Returns:
            True if cleared successfully
        """
        if not self.connected or not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys('proposal:*')
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️ Cache cleared: {deleted} keys deleted")
                return True
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> RedisCacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = RedisCacheManager()
    return _cache_manager

