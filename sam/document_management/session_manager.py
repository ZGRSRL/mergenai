#!/usr/bin/env python3
"""
Requests Session Manager
Provides centralized session management with caching and connection reuse
"""

import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import time
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class SessionManager:
    """Centralized session manager with connection pooling and caching"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.session = None
            self._create_session()
    
    def _create_session(self):
        """Create optimized session with retry strategy"""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configure HTTP adapter
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'SAM-Document-Manager/2.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        logger.info("Session manager initialized with connection pooling")
    
    def get_session(self) -> requests.Session:
        """Get the shared session instance"""
        return self.session
    
    def get_cached_session(self) -> requests.Session:
        """Get session from Streamlit cache"""
        if 'http_session' not in st.session_state:
            st.session_state['http_session'] = self.session
        return st.session_state['http_session']
    
    def close_session(self):
        """Close the session"""
        if self.session:
            self.session.close()
            logger.info("Session closed")

# Global session manager
session_manager = SessionManager()

@st.cache_resource
def get_cached_session():
    """Get cached session for Streamlit"""
    return session_manager.get_session()

class OptimizedHTTPClient:
    """Optimized HTTP client with caching and connection reuse"""
    
    def __init__(self):
        self.session = get_cached_session()
        self.request_count = 0
        self.cache_hits = 0
    
    def get(self, url: str, params: Dict[str, Any] = None, 
            headers: Dict[str, str] = None, timeout: int = 30) -> requests.Response:
        """Optimized GET request with caching"""
        self.request_count += 1
        
        # Add cache headers if not present
        if headers is None:
            headers = {}
        
        if 'Cache-Control' not in headers:
            headers['Cache-Control'] = 'max-age=300'  # 5 minutes
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=timeout
            )
            
            # Log cache status
            if response.headers.get('X-Cache') == 'HIT':
                self.cache_hits += 1
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP GET request failed: {e}")
            raise
    
    def post(self, url: str, data: Dict[str, Any] = None, 
             json: Dict[str, Any] = None, headers: Dict[str, str] = None, 
             timeout: int = 30) -> requests.Response:
        """Optimized POST request"""
        self.request_count += 1
        
        if headers is None:
            headers = {}
        
        try:
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout
            )
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP POST request failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP client statistics"""
        return {
            'request_count': self.request_count,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': (self.cache_hits / self.request_count * 100) if self.request_count > 0 else 0,
            'session_active': self.session is not None
        }

# Global HTTP client
http_client = OptimizedHTTPClient()

# Convenience functions
def get_session() -> requests.Session:
    """Get shared session instance"""
    return session_manager.get_session()

def get_cached_session() -> requests.Session:
    """Get cached session for Streamlit"""
    return get_cached_session()

def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request using optimized client"""
    if method.upper() == 'GET':
        return http_client.get(url, **kwargs)
    elif method.upper() == 'POST':
        return http_client.post(url, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

def get_http_stats() -> Dict[str, Any]:
    """Get HTTP client statistics"""
    return http_client.get_stats()

# Rate limiting utilities
class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_second: float = 0.33):  # 3 second interval
        self.calls_per_second = calls_per_second
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            current_time = time.time()
            time_since_last_call = current_time - self.last_call_time
            
            if time_since_last_call < (1.0 / self.calls_per_second):
                sleep_time = (1.0 / self.calls_per_second) - time_since_last_call
                logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            self.last_call_time = time.time()

# Global rate limiter
rate_limiter = RateLimiter()

def apply_rate_limit():
    """Apply rate limiting"""
    rate_limiter.wait_if_needed()

# Session cleanup on app shutdown
def cleanup_sessions():
    """Cleanup sessions on app shutdown"""
    session_manager.close_session()
    logger.info("Sessions cleaned up")

# Initialize session manager
if __name__ == "__main__":
    # Test the session manager
    print("Testing Session Manager...")
    
    session = get_session()
    print(f"✅ Session created: {session is not None}")
    
    stats = get_http_stats()
    print(f"📊 HTTP Stats: {stats}")
    
    # Test rate limiter
    print("Testing rate limiter...")
    start_time = time.time()
    apply_rate_limit()
    apply_rate_limit()
    end_time = time.time()
    print(f"⏱️ Rate limiter test completed in {end_time - start_time:.2f} seconds")
