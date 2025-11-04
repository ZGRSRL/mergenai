# -*- coding: utf-8 -*-
import requests, time, math, logging, hashlib, json
from typing import List, Dict, Tuple
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'document_management'))
from database_manager import execute_query

UA = {"User-Agent": "ZGR-HotelFinder/1.0 (+contact: ops@zgr.local)"}
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"

class RateLimiter:
    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self.last = 0.0
    def wait(self):
        now = time.time()
        delta = now - self.last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self.last = time.time()

rl = RateLimiter(1.2)

def _cache_key(bbox):
    raw = f"{bbox[0]:.4f},{bbox[1]:.4f},{bbox[2]:.4f},{bbox[3]:.4f}"
    return hashlib.sha1(raw.encode()).hexdigest()

def cache_get(bbox):
    k = _cache_key(bbox)
    row = execute_query("SELECT payload FROM osm_cache WHERE key=%s AND created_at > now() - interval '24 hours'", (k,), fetch=True)
    return row[0][0] if row else None

def cache_put(bbox, payload):
    k = _cache_key(bbox)
    execute_query("INSERT INTO osm_cache(key, payload) VALUES(%s, %s::jsonb) ON CONFLICT (key) DO UPDATE SET payload=EXCLUDED.payload, created_at=now()", (k, json.dumps(payload)), fetch=False)

def geocode_city(place_name: str) -> Tuple[float,float,Tuple[float,float,float,float]]:
    """Return (lat, lon, bbox=(south, west, north, east))."""
    rl.wait()
    r = requests.get(NOMINATIM_URL, params={"q": place_name, "format":"json", "limit":1}, headers=UA, timeout=30)
    r.raise_for_status()
    arr = r.json()
    if not arr:
        raise ValueError(f"Place not found: {place_name}")
    itm = arr[0]
    lat = float(itm["lat"]); lon = float(itm["lon"])
    # Nominatim boundingbox: [south, north, west, east] -> convert to (south, west, north, east)
    bb = [float(x) for x in itm["boundingbox"]]  # [south, north, west, east]
    south, north, west, east = bb[0], bb[1], float(itm["lon"]) - 0.08, float(itm["lon"]) + 0.08
    # west/east küçük bir tamponla ayarlandı; istersen itm["boundingbox"][2:4] kullan.
    return lat, lon, (south, west, north, east)

def overpass_hotels(bbox: Tuple[float,float,float,float]) -> List[Dict]:
    """Query OSM hotels within bbox."""
    # Check cache first (temporarily disabled)
    try:
        cached = cache_get(bbox)
        if cached:
            return cached.get("elements", [])
    except:
        pass  # Cache not available, continue with API call
    
    south, west, north, east = bbox
    q = f"""
    [out:json][timeout:30];
    (
      node["tourism"="hotel"]({south},{west},{north},{east});
      way["tourism"="hotel"]({south},{west},{north},{east});
      relation["tourism"="hotel"]({south},{west},{north},{east});
    );
    out center tags 200;
    """
    for attempt in range(5):
        try:
            rl.wait()
            r = requests.post(OVERPASS_URL, data=q, headers=UA, timeout=60)
            r.raise_for_status()
            result = r.json()
            # Cache the result (temporarily disabled)
            try:
                cache_put(bbox, result)
            except:
                pass  # Cache not available
            return result.get("elements", [])
        except requests.HTTPError as e:
            logging.warning(f"Overpass HTTP error {e} attempt {attempt+1}/5")
            time.sleep(2*(attempt+1))
    return []

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    from math import radians, sin, cos, atan2, sqrt
    dlat = radians(lat2-lat1); dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))
