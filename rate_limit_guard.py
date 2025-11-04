#!/usr/bin/env python3
"""
Rate Limit Guard - Exponential backoff + jitter for API calls
"""

import time
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    base_delay: float = 1.0
    max_delay: float = 32.0
    jitter_range: float = 0.5
    max_retries: int = 5
    backoff_multiplier: float = 2.0

class RateLimitGuard:
    """Rate limit guard with exponential backoff and jitter"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.logger = logging.getLogger("RateLimitGuard")
        self.global_limiter = {}  # Global rate limiter per endpoint
        
    def backoff_sleep(self, attempt: int, endpoint: str = "default") -> None:
        """Calculate and sleep with exponential backoff + jitter"""
        if attempt <= 0:
            return
            
        # Calculate delay
        delay = min(
            self.config.max_delay,
            self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        )
        
        # Add jitter
        jitter = random.uniform(0, self.config.jitter_range)
        total_delay = delay + jitter
        
        self.logger.info(f"Rate limit backoff: {total_delay:.2f}s (attempt {attempt}, endpoint: {endpoint})")
        time.sleep(total_delay)
    
    def check_global_limit(self, endpoint: str, min_interval: float = 3.0) -> bool:
        """Check global rate limit for endpoint"""
        now = datetime.now()
        
        if endpoint not in self.global_limiter:
            self.global_limiter[endpoint] = now
            return True
        
        last_call = self.global_limiter[endpoint]
        time_since_last = (now - last_call).total_seconds()
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.info(f"Global rate limit: sleeping {sleep_time:.2f}s for {endpoint}")
            time.sleep(sleep_time)
        
        self.global_limiter[endpoint] = datetime.now()
        return True
    
    def execute_with_retry(self, func, *args, endpoint: str = "default", **kwargs) -> Any:
        """Execute function with rate limiting and retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Check global rate limit
                self.check_global_limit(endpoint)
                
                # Execute function
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.info(f"Function succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    self.backoff_sleep(attempt + 1, endpoint)
                else:
                    self.logger.error(f"All {self.config.max_retries + 1} attempts failed")
        
        raise last_exception

# Global rate limit guard instance
rate_guard = RateLimitGuard()

def backoff_sleep(attempt: int, base: float = 1.0, cap: float = 32.0) -> None:
    """Convenience function for backoff sleep"""
    config = RateLimitConfig(base_delay=base, max_delay=cap)
    guard = RateLimitGuard(config)
    guard.backoff_sleep(attempt)

def execute_with_retry(func, *args, endpoint: str = "default", **kwargs) -> Any:
    """Convenience function for executing with retry"""
    return rate_guard.execute_with_retry(func, *args, endpoint=endpoint, **kwargs)

if __name__ == "__main__":
    # Test the rate limit guard
    print("Testing Rate Limit Guard...")
    
    def test_function(success_on_attempt: int = 3):
        """Test function that fails first few times"""
        if not hasattr(test_function, 'call_count'):
            test_function.call_count = 0
        
        test_function.call_count += 1
        
        if test_function.call_count < success_on_attempt:
            raise Exception(f"Simulated failure on attempt {test_function.call_count}")
        
        return f"Success on attempt {test_function.call_count}"
    
    # Test with retry
    try:
        result = execute_with_retry(test_function, success_on_attempt=3, endpoint="test")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Test global rate limiting
    print("Testing global rate limiting...")
    start_time = time.time()
    
    for i in range(3):
        rate_guard.check_global_limit("test_endpoint", min_interval=1.0)
        print(f"Call {i + 1} at {time.time() - start_time:.2f}s")
    
    print("Rate Limit Guard test completed!")

