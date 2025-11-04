# -*- coding: utf-8 -*-
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'document_management'))
from database_manager import execute_query

def save_hotel_suggestions(notice_id: str, items: List[Dict[str,Any]]) -> int:
    import json
    q = """
    INSERT INTO hotel_suggestions
    (notice_id, name, address, phone, website, lat, lon, capacity_estimate, price_estimate, distance_km, match_score, provenance)
    VALUES
    (%(notice_id)s, %(name)s, %(address)s, %(phone)s, %(website)s, %(lat)s, %(lon)s, %(capacity_estimate)s, %(price_estimate)s, %(distance_km)s, %(match_score)s, %(provenance)s::jsonb)
    """
    count = 0
    for it in items:
        params = dict(it)
        params["notice_id"] = notice_id
        params["provenance"] = json.dumps(params.get("provenance") or {})
        execute_query(q, params, fetch=False)
        count += 1
    return count

def list_hotel_suggestions(notice_id: str, limit: int = 50) -> List[Dict[str,Any]]:
    q = """
    SELECT name, address, phone, website, lat, lon, distance_km, match_score
    FROM hotel_suggestions
    WHERE notice_id=%s
    ORDER BY match_score DESC, distance_km ASC
    LIMIT %s
    """
    rows = execute_query(q, (notice_id, limit), fetch=True) or []
    return [
        {"name": r[0], "address": r[1], "phone": r[2], "website": r[3],
         "lat": r[4], "lon": r[5], "distance_km": r[6], "match_score": r[7]}
        for r in rows
    ]
