#!/usr/bin/env python3
"""
Safe SAM API Client with proper rate limiting and Retry-After parsing
"""

import os
import time
import requests
import random
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SamClientSafe:
    """Safe SAM API client with rate limiting and proper error handling"""
    
    def __init__(self, base=None, key=None, sys_key=None, min_interval=5.0):
        self.base = (base or os.getenv("SAM_OPPS_BASE_URL") or "https://api.sam.gov/opportunities/v2").rstrip("/")
        self.key = (key or os.getenv("SAM_API_KEY") or os.getenv("SAM_PUBLIC_API_KEY") or "").strip()
        self.sys_key = (sys_key or os.getenv("SAM_API_KEY_SYSTEM") or "").strip()
        self.min_interval = float(os.getenv("SAM_MIN_INTERVAL", min_interval))
        self.last_call = 0.0
        
        if not self.key:
            raise ValueError("No SAM API key found. Set SAM_API_KEY in .env file.")
        
        logger.info(f"SamClientSafe initialized - Base: {self.base}, Key: {self.key[:10]}...")

    def _parse_retry_after(self, v):
        """Parse Retry-After header (both seconds and HTTP-date format)"""
        if not v:
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            try:
                dt = parsedate_to_datetime(v)
                now = parsedate_to_datetime(time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
                return max((dt - now).total_seconds(), 0.0)
            except Exception:
                return 0.0

    def _respect_interval(self):
        """Respect minimum interval between requests"""
        dt = time.time() - self.last_call
        if dt < self.min_interval:
            wait_time = self.min_interval - dt
            logger.debug(f"Respecting min interval: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        self.last_call = time.time()

    def _request(self, path, params, retries=5):
        """Make safe request with rate limiting and retry logic"""
        url = urljoin(self.base + "/", path.lstrip("/"))
        params = dict(params or {})
        params.setdefault("api_key", self.key)
        sleep = 2.0

        for attempt in range(1, retries + 1):
            self._respect_interval()
            
            logger.info(f"Making request (attempt {attempt}/{retries}) to {url}")
            r = requests.get(url, params=params, timeout=60)
            rh = {k.lower(): v for k, v in r.headers.items()}
            
            logger.info(f"Response: {r.status_code}, Rate Limit Used: {rh.get('x-ratelimit-used', 'N/A')}, "
                       f"Remaining: {rh.get('x-ratelimit-remaining', 'N/A')}")
            
            if r.status_code == 429:
                ra = self._parse_retry_after(rh.get("retry-after"))
                wait = max(ra, sleep) + random.uniform(0, 0.5)  # Add jitter
                logger.warning(f"Rate limited (429). Waiting {wait:.1f}s (Retry-After: {ra:.1f}s, Backoff: {sleep:.1f}s)...")
                time.sleep(wait)
                sleep = min(sleep * 2, 60)  # Exponential backoff
                continue
                
            if r.status_code in (401, 403) and self.sys_key and params.get("api_key") != self.sys_key:
                # Fallback to system key
                logger.info("Public key failed, trying system key...")
                params["api_key"] = self.sys_key
                continue
                
            r.raise_for_status()
            return r
            
        raise RuntimeError("Rate limit veya yetki: denemeler tükendi")

    def search(self, **params):
        """Search opportunities with safe rate limiting"""
        try:
            response = self._request("/search", params)
            return response.json()
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_opportunity(self, notice_id):
        """Get specific opportunity by notice ID"""
        try:
            data = self.search(noticeid=notice_id, limit="1")
            opportunities = data.get("opportunitiesData", [])
            return opportunities[0] if opportunities else None
        except Exception as e:
            logger.error(f"Failed to get opportunity {notice_id}: {e}")
            return None

    def search_recent(self, days=7, limit=10, **filters):
        """Search recent opportunities with safe parameters"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "postedFrom": start_date.strftime("%m/%d/%Y"),
            "postedTo": end_date.strftime("%m/%d/%Y"),
            "limit": str(limit),
            **filters
        }
        
        return self.search(**params)

    def test_connection(self):
        """Test API connection with minimal request"""
        try:
            # Use a very specific search with date range to minimize load
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            data = self.search(
                postedFrom=start_date.strftime("%m/%d/%Y"),
                postedTo=end_date.strftime("%m/%d/%Y"),
                limit="1"
            )
            return "opportunitiesData" in data
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

def test_safe_client():
    """Test the safe SAM client"""
    print("Testing Safe SAM API Client")
    print("=" * 40)
    
    try:
        # Initialize client
        client = SamClientSafe()
        print(f"[SUCCESS] Client initialized")
        print(f"  - Base URL: {client.base}")
        print(f"  - API Key: {client.key[:10]}...")
        print(f"  - Min Interval: {client.min_interval}s")
        
        # Test connection
        print(f"\n[TEST] Testing connection...")
        if client.test_connection():
            print("[SUCCESS] Connection test passed!")
        else:
            print("[ERROR] Connection test failed!")
            return False
        
        # Test specific opportunity
        print(f"\n[TEST] Testing specific opportunity...")
        notice_id = "70LART26QPFB00001"
        opportunity = client.get_opportunity(notice_id)
        
        if opportunity:
            print(f"[SUCCESS] Found opportunity: {notice_id}")
            print(f"  - Title: {opportunity.get('title', 'N/A')}")
            print(f"  - Agency: {opportunity.get('department', 'N/A')}")
        else:
            print(f"[WARNING] Opportunity {notice_id} not found")
        
        # Test recent search
        print(f"\n[TEST] Testing recent search...")
        recent_data = client.search_recent(days=30, limit=3)
        opportunities = recent_data.get("opportunitiesData", [])
        
        if opportunities:
            print(f"[SUCCESS] Found {len(opportunities)} recent opportunities")
            for i, opp in enumerate(opportunities, 1):
                print(f"  {i}. {opp.get('title', 'No Title')} ({opp.get('noticeId', 'N/A')})")
        else:
            print("[WARNING] No recent opportunities found")
        
        print(f"\n[SUCCESS] Safe SAM API Client test completed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_safe_client()
