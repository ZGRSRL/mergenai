#!/usr/bin/env python3
"""
API Health Check Module
Real-time health monitoring for RAG API and Redis
"""

import os
import time
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def check_rag_api_health(api_url: str, timeout: int = 3) -> Dict[str, Any]:
    """
    Check RAG API health status
    
    Args:
        api_url: RAG API base URL
        timeout: Request timeout in seconds
        
    Returns:
        Health status dict with status, response_time, and details
    """
    # Try multiple health endpoint variations
    base_url = api_url.rstrip('/')
    health_endpoints = [
        f"{base_url}/health",
        f"{base_url}/api/health",
        f"{base_url}/api/rag/health"
    ]
    
    # Try each health endpoint
    last_error = None
    for health_url in health_endpoints:
        try:
            start_time = time.time()
            response = requests.get(health_url, timeout=timeout)
            response_time = round((time.time() - start_time) * 1000, 2)  # milliseconds
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'endpoint': health_url,
                    'timestamp': datetime.now().isoformat(),
                    'error': None
                }
            elif response.status_code in [404, 405]:
                # Endpoint not found, try next
                last_error = f"HTTP {response.status_code} - {health_url}"
                continue
            else:
                return {
                    'status': 'degraded',
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'endpoint': health_url,
                    'timestamp': datetime.now().isoformat(),
                    'error': f"HTTP {response.status_code}"
                }
        except requests.exceptions.Timeout:
            last_error = f'Timeout after {timeout}s - {health_url}'
            continue
        except requests.exceptions.ConnectionError:
            last_error = f'Connection refused - {health_url}'
            continue
        except Exception as e:
            last_error = f'{str(e)} - {health_url}'
            continue
    
    # All endpoints failed
    try:
        start_time = time.time()
        # Try base URL as fallback
        response = requests.get(base_url, timeout=timeout)
        response_time = round((time.time() - start_time) * 1000, 2)
        if response.status_code < 500:
            return {
                'status': 'degraded',
                'response_time_ms': response_time,
                'status_code': response.status_code,
                'endpoint': base_url,
                'timestamp': datetime.now().isoformat(),
                'error': 'Health endpoint not found, but API is reachable'
            }
    except:
        pass
    
    # All attempts failed
    return {
        'status': 'offline',
        'response_time_ms': None,
        'status_code': None,
        'timestamp': datetime.now().isoformat(),
        'error': last_error or 'Connection failed'
    }

def get_health_status_icon(status: str) -> str:
    """
    Get status icon for display
    
    Args:
        status: Health status ('healthy', 'degraded', 'timeout', 'offline', 'error')
        
    Returns:
        Emoji icon string
    """
    icons = {
        'healthy': '🟢',
        'degraded': '🟡',
        'timeout': '🟡',
        'offline': '🔴',
        'error': '🔴'
    }
    return icons.get(status, '⚪')

def get_health_status_text(status: str) -> str:
    """
    Get human-readable status text
    
    Args:
        status: Health status
        
    Returns:
        Status text string
    """
    texts = {
        'healthy': 'Healthy',
        'degraded': 'Degraded',
        'timeout': 'Timeout',
        'offline': 'Offline',
        'error': 'Error'
    }
    return texts.get(status, 'Unknown')

def check_redis_health(redis_manager) -> Dict[str, Any]:
    """
    Check Redis cache health
    
    Args:
        redis_manager: RedisCacheManager instance
        
    Returns:
        Health status dict
    """
    if not redis_manager or not redis_manager.connected:
        return {
            'status': 'offline',
            'connected': False,
            'timestamp': datetime.now().isoformat(),
            'error': 'Redis not connected'
        }
    
    try:
        stats = redis_manager.get_stats()
        return {
            'status': 'healthy' if stats.get('connected') else 'offline',
            'connected': stats.get('connected', False),
            'keys': stats.get('keys', 0),
            'memory_mb': stats.get('memory_mb', 0.0),
            'timestamp': datetime.now().isoformat(),
            'error': None
        }
    except Exception as e:
        return {
            'status': 'error',
            'connected': False,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

