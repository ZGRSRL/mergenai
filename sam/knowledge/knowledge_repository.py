#!/usr/bin/env python3
"""
Knowledge Repository - DB erişimi
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any, List
import json

# Database import with fallback
try:
    from sam.document_management.database_manager import execute_query
except ImportError:
    def execute_query(query, params=None, fetch=True):
        print(f"Mock execute_query: {query[:50]}...")
        return []

class KnowledgeRepository:
    """Knowledge facts için veritabanı işlemleri"""
    
    @staticmethod
    def upsert(notice_id: str, payload: Dict[str, Any], source_docs: Optional[List[Dict]] = None) -> Optional[str]:
        """Knowledge facts'i kaydet veya güncelle"""
        q = """
        INSERT INTO knowledge_facts (notice_id, payload, source_docs)
        VALUES (%s, %s::jsonb, %s::jsonb)
        ON CONFLICT (id) DO NOTHING
        RETURNING id;
        """
        try:
            result = execute_query(q, (notice_id, json.dumps(payload), json.dumps(source_docs or [])), fetch=True)
            return result[0][0] if result else None
        except Exception as e:
            print(f"Knowledge upsert error: {e}")
            return None
    
    @staticmethod
    def latest(notice_id: str) -> Optional[Dict[str, Any]]:
        """Notice için en son knowledge facts'i getir"""
        q = """
        SELECT id, payload, source_docs, created_at 
        FROM knowledge_facts 
        WHERE notice_id=%s 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        try:
            rows = execute_query(q, (notice_id,), fetch=True)
            if rows:
                row = rows[0]
                return {
                    "id": row[0],
                    "payload": row[1],
                    "source_docs": row[2],
                    "created_at": row[3]
                }
            return None
        except Exception as e:
            print(f"Knowledge latest error: {e}")
            return None
    
    @staticmethod
    def list_for_notice(notice_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Notice için tüm knowledge facts'leri listele"""
        q = """
        SELECT id, payload, created_at 
        FROM knowledge_facts 
        WHERE notice_id=%s 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        try:
            rows = execute_query(q, (notice_id, limit), fetch=True)
            return [
                {
                    "id": row[0],
                    "payload": row[1],
                    "created_at": row[2]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Knowledge list error: {e}")
            return []
    
    @staticmethod
    def get_summary_view(notice_id: str) -> Optional[Dict[str, Any]]:
        """vw_knowledge_summary view'ından özet bilgi getir"""
        q = """
        SELECT 
            notice_id,
            period,
            rooms_per_night,
            projector_lumens_min,
            fire_safety_required,
            sca_applicable,
            tax_exempt,
            created_at
        FROM vw_knowledge_summary 
        WHERE notice_id=%s 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        try:
            rows = execute_query(q, (notice_id,), fetch=True)
            if rows:
                row = rows[0]
                return {
                    "notice_id": row[0],
                    "period": row[1],
                    "rooms_per_night": row[2],
                    "projector_lumens_min": row[3],
                    "fire_safety_required": row[4],
                    "sca_applicable": row[5],
                    "tax_exempt": row[6],
                    "created_at": row[7]
                }
            return None
        except Exception as e:
            print(f"Knowledge summary error: {e}")
            return None
    
    @staticmethod
    def delete_for_notice(notice_id: str) -> bool:
        """Notice için tüm knowledge facts'leri sil"""
        q = "DELETE FROM knowledge_facts WHERE notice_id=%s"
        try:
            execute_query(q, (notice_id,), fetch=False)
            return True
        except Exception as e:
            print(f"Knowledge delete error: {e}")
            return False
