# -*- coding: utf-8 -*-
from typing import Dict, List
import time
from sam.hotels.hotel_osm_client import geocode_city, overpass_hotels, haversine_km

# Import log manager
try:
    from agent_log_manager import log_agent_action
except ImportError:
    def log_agent_action(*args, **kwargs):
        pass  # Silent fallback

def _dig(d: Dict, path: List[str], default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur

def compute_match_score(distance_km: float, capacity_req: int, has_phone: bool, has_website: bool) -> float:
    # distance-based (<=5km iyi), contact bonus
    base = max(0.0, 1.0 - min(distance_km/10.0, 1.0))   # 0..1
    bonus = (0.05 if has_phone else 0.0) + (0.05 if has_website else 0.0)
    score = min(1.0, round(base + bonus, 3))
    return score

def run_hotel_finder_from_sow(sow_payload: Dict, notice_id: str = None) -> List[Dict]:
    """
    Input: SOW JSON (schema_version: sow.v1.1)
    Output: top hotel suggestions [{...}]
    """
    start_time = time.time()
    
    city = _dig(sow_payload, ["location","city"]) or _dig(sow_payload, ["location","name"]) or "Artesia, NM"
    capacity = _dig(sow_payload, ["function_space","general_session","capacity"], 100)
    rooms_per_night = _dig(sow_payload, ["room_block","total_rooms_per_night"], 80)

    lat, lon, bbox = geocode_city(city)
    elements = overpass_hotels(bbox)

    suggestions = []
    for e in elements:
        tags = e.get("tags", {})
        # center coords for ways/relations, or lat/lon for nodes
        hlat = e.get("lat") or (e.get("center") or {}).get("lat")
        hlon = e.get("lon") or (e.get("center") or {}).get("lon")
        if not hlat or not hlon:
            continue

        name = tags.get("name") or tags.get("brand")
        if not name: 
            continue

        phone   = tags.get("phone") or tags.get("contact:phone")
        website = tags.get("website") or tags.get("contact:website")
        address = ", ".join(filter(None, [
            tags.get("addr:housenumber"), tags.get("addr:street"),
            tags.get("addr:city"), tags.get("addr:state"), tags.get("addr:postcode")
        ]))

        distance = round(haversine_km(lat, lon, float(hlat), float(hlon)), 2)
        score = compute_match_score(distance, capacity, bool(phone), bool(website))

        suggestions.append({
            "name": name,
            "address": address or None,
            "phone": phone or None,
            "website": website or None,
            "lat": float(hlat),
            "lon": float(hlon),
            "distance_km": distance,
            "match_score": score,
            "capacity_estimate": None,   # OSM'de çoğunlukla yok; gelecekte Wikidata ile zenginleştirilebilir
            "price_estimate": None,
            "provenance": {
                "source": "OSM",
                "tags_present": list(tags.keys())[:10]
            }
        })

    # sıralama: en yakın / en yüksek puan
    suggestions.sort(key=lambda x: (-(x["match_score"]), x["distance_km"]))
    results = suggestions[:10]
    
    # Log agent action
    if notice_id:
        processing_time = time.time() - start_time
        log_agent_action(
            agent_name="HotelFinderAgent",
            notice_id=notice_id,
            action="find_hotels_from_sow",
            input_data={"city": city, "capacity": capacity, "rooms_per_night": rooms_per_night},
            output_data={"count": len(results), "city": city},
            processing_time=processing_time,
            status="success",
            schema_version="sow.v1.1",
            source_docs=["osm", "nominatim"]
        )
    
    return results
