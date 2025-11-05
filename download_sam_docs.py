#!/usr/bin/env python3
"""
SAM.gov Document Downloader with proper rate limiting and error handling
Downloads documents for archived opportunities like 70LART26QPFB00001
"""

import os
import time
import json
import re
import random
from pathlib import Path
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

SAM_BASE = os.getenv("SAM_OPPS_BASE_URL", "https://api.sam.gov/opportunities/v2").rstrip("/")
PUB_KEY = (os.getenv("SAM_API_KEY") or os.getenv("SAM_PUBLIC_API_KEY") or "").strip()
SYS_KEY = (os.getenv("SAM_API_KEY_SYSTEM") or "").strip()

MIN_INTERVAL = float(os.getenv("SAM_MIN_INTERVAL", "5"))  # saniye

def _parse_retry_after(v: str | None) -> float:
    """Parse Retry-After header (both seconds and HTTP-date format)"""
    if not v:
        return 0.0
    v = v.strip()
    try:
        return float(v)
    except ValueError:
        try:
            dt = parsedate_to_datetime(v)
            now = parsedate_to_datetime(time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
            return max((dt - now).total_seconds(), 0.0)
        except Exception:
            return 0.0

def _wait_since(last_call: list[float]):
    """Respect minimum interval between requests"""
    dt = time.time() - last_call[0]
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    last_call[0] = time.time()

def _get(url: str, params: dict, last_call: list[float], key_cycle: list[str], retries=6):
    """Safe GET request with rate limiting and retry logic"""
    sleep = 2.0
    for attempt in range(1, retries + 1):
        _wait_since(last_call)
        k = key_cycle[0]
        params = {**params, "api_key": k}
        
        print(f"  [ATTEMPT {attempt}] GET {url}")
        r = requests.get(url, params=params, timeout=90, stream=True)
        rh = {k.lower(): v for k, v in r.headers.items()}
        
        print(f"    Status: {r.status_code}, Rate Limit: {rh.get('x-ratelimit-used', 'N/A')}/{rh.get('x-ratelimit-remaining', 'N/A')}")

        if r.status_code == 429:
            ra = _parse_retry_after(rh.get("retry-after"))
            wait = max(ra, sleep) + random.uniform(0, 0.5)
            print(f"    Rate limited. Waiting {wait:.1f}s...")
            time.sleep(wait)
            sleep = min(sleep * 2, 60)
            continue

        if r.status_code in (401, 403) and SYS_KEY and key_cycle[0] != SYS_KEY:
            # Fallback to system key
            print(f"    Public key failed, trying system key...")
            key_cycle[0] = SYS_KEY
            continue

        if r.status_code >= 500 and attempt < retries:
            # Server error: wait and retry
            print(f"    Server error {r.status_code}. Waiting {sleep:.1f}s...")
            time.sleep(sleep)
            sleep = min(sleep * 2, 60)
            continue

        r.raise_for_status()
        return r
    raise RuntimeError(f"GET failed after retries: {url}")

def fetch_resource_links(notice_id: str, posted_from="10/01/2024", posted_to="11/30/2024", status="archived"):
    """Fetch resource links for a specific opportunity"""
    print(f"[SEARCH] Fetching resource links for {notice_id}")
    print(f"  Date range: {posted_from} to {posted_to}")
    print(f"  Status: {status}")
    
    url = f"{SAM_BASE}/search"
    last_call = [0.0]
    key_cycle = [PUB_KEY or SYS_KEY]
    params = {
        "noticeid": notice_id,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "status": status,
        "limit": "1",
    }
    
    try:
        r = _get(url, params, last_call, key_cycle)
        data = r.json()
        opps = data.get("opportunitiesData") or []
        
        if not opps:
            print(f"  [WARNING] No opportunities found")
            return []
        
        opp = opps[0]
        print(f"  [SUCCESS] Found opportunity: {opp.get('title', 'N/A')}")
        
        resource_links = opp.get("resourceLinks") or []
        print(f"  [INFO] Found {len(resource_links)} resource links")
        
        return resource_links
        
    except Exception as e:
        print(f"  [ERROR] Failed to fetch resource links: {e}")
        return []

def _sanitize_filename(name: str) -> str:
    """Sanitize filename for safe filesystem storage"""
    name = re.sub(r"[^\w\-.]+", "_", name.strip())
    return name[:180]  # Truncate if too long

def _derive_filename(r, fallback: str) -> str:
    """Extract filename from Content-Disposition header"""
    cd = r.headers.get("Content-Disposition", "")
    m = re.search(r'filename\*=UTF-8\'\'([^;]+)', cd)
    if m:
        return _sanitize_filename(requests.utils.unquote(m.group(1)))
    m = re.search(r'filename="?([^"]+)"?', cd)
    if m:
        return _sanitize_filename(m.group(1))
    return _sanitize_filename(fallback)

def _is_pdf_head(first_bytes: bytes) -> bool:
    """Check if bytes start with PDF signature"""
    return first_bytes.startswith(b"%PDF-")

def download_attachment(url: str, out_dir: Path, base_name: str, last_call: list[float]):
    """Download a single attachment with multiple fallback strategies"""
    print(f"\n[DOWNLOAD] {base_name}")
    print(f"  URL: {url}")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    key_cycle = [PUB_KEY or SYS_KEY]

    # Try different URL variations
    try_urls = [url]

    # Add API key if not present
    if "api_key=" not in url:
        sep = "&" if "?" in url else "?"
        try_urls.append(f"{url}{sep}api_key={(PUB_KEY or SYS_KEY)}")

    # Try /download suffix
    if not url.endswith("/download"):
        try_urls.append(url.rstrip("/") + "/download")

    # Try alternative attachment URL format
    m = re.search(r"/attachments/(\d+)", url)
    if m:
        att_id = m.group(1)
        alt = f"https://sam.gov/api/prod/attachments/{att_id}/download"
        if alt not in try_urls:
            try_urls.append(alt)

    last_exc = None
    for attempt, u in enumerate(try_urls, 1):
        try:
            print(f"  [TRY {attempt}] {u}")
            
            # Get the file
            r = _get(u, {}, last_call, key_cycle)
            
            # Check content type and first bytes
            head = b"".join(next(iter((chunk for chunk in r.iter_content(1024) if chunk)), b""))
            content_type = r.headers.get("Content-Type", "")
            
            print(f"    Content-Type: {content_type}")
            print(f"    Content-Length: {r.headers.get('Content-Length', 'Unknown')}")
            
            # Download the file
            r2 = _get(u, {}, last_call, key_cycle)
            fname = _derive_filename(r2, f"{base_name}.pdf")
            out_path = out_dir / fname
            
            print(f"    Saving to: {out_path}")
            
            with open(out_path, "wb") as f:
                for chunk in r2.iter_content(1 << 20):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
            
            # Validate file
            with open(out_path, "rb") as f:
                sig = f.read(5)
            
            file_size = os.path.getsize(out_path)
            print(f"    File size: {file_size} bytes")
            
            if "pdf" in content_type.lower() or _is_pdf_head(sig):
                print(f"    [SUCCESS] Valid PDF file")
                return out_path
            else:
                print(f"    [WARNING] Non-PDF content-type: {content_type}")
                return out_path
                
        except Exception as e:
            last_exc = e
            print(f"    [ERROR] Attempt {attempt} failed: {e}")
            continue
    
    raise last_exc or RuntimeError("All attempts failed")

def main():
    """Main function"""
    print("SAM.gov Document Downloader")
    print("=" * 50)
    
    NOTICE = os.getenv("NOTICE_ID", "70LART26QPFB00001")
    OUT = Path(os.getenv("DOWNLOAD_PATH", "./downloads")) / NOTICE
    
    if not (PUB_KEY or SYS_KEY):
        print("[ERROR] No SAM_API_KEY / SAM_PUBLIC_API_KEY set")
        print("Please set your API key in .env file or environment variable")
        return False
    
    print(f"Notice ID: {NOTICE}")
    print(f"Output Directory: {OUT}")
    print(f"API Key: {(PUB_KEY or SYS_KEY)[:10]}...")
    print()
    
    # Fetch resource links
    links = fetch_resource_links(NOTICE)
    
    if not links:
        print("[WARNING] No resourceLinks found in API")
        print("This could mean:")
        print("  - Opportunity is not archived")
        print("  - Different date range needed")
        print("  - API access issues")
        return False
    
    # Download each attachment
    print(f"\n[DOWNLOAD] Starting download of {len(links)} files...")
    last_call = [0.0]
    ok = 0
    
    for i, link in enumerate(links, 1):
        base_name = f"{NOTICE}_{i}"
        try:
            p = download_attachment(link, OUT, base_name, last_call)
            print(f"[SUCCESS] Downloaded: {p}")
            ok += 1
        except Exception as e:
            print(f"[FAILED] {link} -> {e}")
    
    print(f"\n[SUMMARY] Downloaded {ok}/{len(links)} files successfully")
    
    if ok == 0:
        print("[ERROR] No files were downloaded")
        return False
    else:
        print(f"[SUCCESS] Files saved to: {OUT.absolute()}")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)













