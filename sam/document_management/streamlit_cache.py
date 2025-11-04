#!/usr/bin/env python3
"""
Streamlit Caching Utilities
Provides caching decorators to reduce API calls and improve performance
"""

import streamlit as st
import functools
import hashlib
import time
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class StreamlitCacheManager:
    """Centralized cache management for Streamlit app"""
    
    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_calls': 0
        }
    
    def get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key from function name and arguments"""
        # Create a hash of the arguments
        args_str = str(args) + str(sorted(kwargs.items()))
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        return f"{func_name}_{args_hash}"
    
    def log_cache_stats(self, hit: bool):
        """Log cache statistics"""
        self.cache_stats['total_calls'] += 1
        if hit:
            self.cache_stats['hits'] += 1
        else:
            self.cache_stats['misses'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_stats['total_calls']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
        return {
            **self.cache_stats,
            'hit_rate': hit_rate
        }

# Global cache manager instance
cache_manager = StreamlitCacheManager()

def cached_api_call(ttl: int = 300, max_entries: int = 100):
    """
    Decorator for caching API calls with TTL
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        max_entries: Maximum number of cached entries
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.get_cache_key(func.__name__, *args, **kwargs)
            
            # Check if cached result exists
            if cache_key in st.session_state:
                cached_data = st.session_state[cache_key]
                if time.time() - cached_data['timestamp'] < ttl:
                    cache_manager.log_cache_stats(True)
                    logger.info(f"Cache HIT for {func.__name__}")
                    return cached_data['result']
            
            # Cache miss - call function
            cache_manager.log_cache_stats(False)
            logger.info(f"Cache MISS for {func.__name__}")
            
            result = func(*args, **kwargs)
            
            # Store in cache
            st.session_state[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            # Clean old entries if needed
            if len(st.session_state) > max_entries:
                self._clean_old_cache_entries(ttl)
            
            return result
        
        return wrapper
    return decorator

def cached_database_query(ttl: int = 60):
    """
    Decorator for caching database queries
    
    Args:
        ttl: Time to live in seconds (default: 1 minute)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_manager.get_cache_key(f"db_{func.__name__}", *args, **kwargs)
            
            if cache_key in st.session_state:
                cached_data = st.session_state[cache_key]
                if time.time() - cached_data['timestamp'] < ttl:
                    cache_manager.log_cache_stats(True)
                    return cached_data['result']
            
            cache_manager.log_cache_stats(False)
            result = func(*args, **kwargs)
            
            st.session_state[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            return result
        
        return wrapper
    return decorator

def cached_opportunity_data(ttl: int = 1800):
    """
    Decorator for caching opportunity data (30 minutes)
    
    Args:
        ttl: Time to live in seconds (default: 30 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_manager.get_cache_key(f"opp_{func.__name__}", *args, **kwargs)
            
            if cache_key in st.session_state:
                cached_data = st.session_state[cache_key]
                if time.time() - cached_data['timestamp'] < ttl:
                    cache_manager.log_cache_stats(True)
                    logger.info(f"Opportunity cache HIT for {func.__name__}")
                    return cached_data['result']
            
            cache_manager.log_cache_stats(False)
            logger.info(f"Opportunity cache MISS for {func.__name__}")
            
            result = func(*args, **kwargs)
            
            st.session_state[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            return result
        
        return wrapper
    return decorator

def cached_bulk_fetch(ttl: int = 3600):
    """
    Decorator for caching bulk fetch operations (1 hour)
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_manager.get_cache_key(f"bulk_{func.__name__}", *args, **kwargs)
            
            if cache_key in st.session_state:
                cached_data = st.session_state[cache_key]
                if time.time() - cached_data['timestamp'] < ttl:
                    cache_manager.log_cache_stats(True)
                    logger.info(f"Bulk fetch cache HIT for {func.__name__}")
                    return cached_data['result']
            
            cache_manager.log_cache_stats(False)
            logger.info(f"Bulk fetch cache MISS for {func.__name__}")
            
            result = func(*args, **kwargs)
            
            st.session_state[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            return result
        
        return wrapper
    return decorator

def clear_cache():
    """Clear all cached data"""
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith(('db_', 'opp_', 'bulk_'))]
    for key in keys_to_remove:
        del st.session_state[key]
    
    logger.info(f"Cleared {len(keys_to_remove)} cache entries")

def get_cache_info() -> Dict[str, Any]:
    """Get information about current cache state"""
    cache_keys = [key for key in st.session_state.keys() if key.startswith(('db_', 'opp_', 'bulk_'))]
    
    return {
        'total_cached_items': len(cache_keys),
        'cache_stats': cache_manager.get_stats(),
        'cache_keys': cache_keys[:10]  # Show first 10 keys
    }

def _clean_old_cache_entries(ttl: int):
    """Clean old cache entries"""
    current_time = time.time()
    keys_to_remove = []
    
    for key, value in st.session_state.items():
        if isinstance(value, dict) and 'timestamp' in value:
            if current_time - value['timestamp'] > ttl:
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    logger.info(f"Cleaned {len(keys_to_remove)} old cache entries")

# Cache configuration constants
CACHE_CONFIG = {
    'api_calls': {'ttl': 300, 'max_entries': 100},      # 5 minutes
    'db_queries': {'ttl': 60, 'max_entries': 200},       # 1 minute
    'opportunities': {'ttl': 1800, 'max_entries': 50},   # 30 minutes
    'bulk_fetch': {'ttl': 3600, 'max_entries': 10},      # 1 hour
}

# Convenience functions for common caching patterns
def cache_api_call(func):
    """Cache API calls for 5 minutes"""
    return cached_api_call(**CACHE_CONFIG['api_calls'])(func)

def cache_db_query(func):
    """Cache database queries for 1 minute"""
    return cached_database_query(**CACHE_CONFIG['db_queries'])(func)

def cache_opportunity(func):
    """Cache opportunity data for 30 minutes"""
    return cached_opportunity_data(**CACHE_CONFIG['opportunities'])(func)

def cache_bulk_fetch(func):
    """Cache bulk fetch operations for 1 hour"""
    return cached_bulk_fetch(**CACHE_CONFIG['bulk_fetch'])(func)
