# test_once.py - Minimal SAM API test with backoff and rate limiting
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables
BASE_URL = os.getenv('SAM_OPPS_BASE_URL', 'https://api.sam.gov/opportunities/v2')
API_KEY = os.getenv('SAM_API_KEY_PUBLIC') or os.getenv('SAM_API_KEY')

# Debug: Print API key status
print(f"API_KEY from env: {API_KEY}")
print(f"BASE_URL: {BASE_URL}")

class SimpleRateLimiter:
    def __init__(self, rate_per_minute=10):
        self.capacity = rate_per_minute
        self.tokens = rate_per_minute
        self.refill = rate_per_minute / 60.0  # token/s
        self.lock = False  # Simple lock for demo
        self.last = time.time()

    def acquire(self):
        while True:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill)
            self.last = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            time.sleep(0.25)

limiter = SimpleRateLimiter(rate_per_minute=10)

def get_with_backoff(url, params, max_retries=5, base_sleep=2.0):
    sleep = base_sleep
    for attempt in range(1, max_retries + 1):
        limiter.acquire()  # Rate limit
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 429:
            ra = r.headers.get('Retry-After')
            try:
                wait = float(ra) if ra else sleep
            except (ValueError, TypeError):
                wait = sleep  # Use current sleep time if can't parse
            print(f'Rate limited, waiting {wait}s...')
            time.sleep(wait)
            sleep = min(sleep * 2, 60)  # Exponential backoff
            continue
        r.raise_for_status()
        return r
    raise RuntimeError('Rate limit: retries exhausted')

# Test with minimal load
params = {
    'noticeid': '70LART26QPFB00001',  # Single record
    'limit': '1',
    'api_key': API_KEY
}

try:
    r = get_with_backoff(f'{BASE_URL}/search', params)
    print('STATUS:', r.status_code)
    print('HEADERS:', {k: v for k, v in r.headers.items() if k.lower().startswith(('x-rate', 'retry-after'))})
    data = r.json()
    opp = data.get('opportunitiesData', [{}])[0]
    print('SUCCESS: Found noticeId:', opp.get('noticeId'))
except Exception as e:
    print('ERROR:', e)