#!/usr/bin/env python3
"""
Requirements Manager
AutoGen Agent'lardan gelen extracted_requirements'ları yapılandırılmış olarak kaydeder
"""

import os
import psycopg2
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432")
TABLE_NAME = 'structured_requirements'  # MergenAI requirements tablosu

class RequirementsManager:
    """Requirements yönetimi için manager sınıfı"""
    
    def __init__(self):
        self.db_dsn = DB_DSN
    
    def save_requirements(self, notice_id: str, extracted_requirements: Dict[str, Any], 
                         extracted_by: str = 'autogen_agent') -> bool:
        """
        Extracted requirements'ları requirements tablosuna kaydeder
        
        Args:
            notice_id: SAM.gov Notice ID
            extracted_requirements: AutoGen agent'tan gelen requirements dict
            extracted_by: Extraction yapan agent (default: 'autogen_agent')
            
        Returns:
            True if successful
        """
        try:
            conn = psycopg2.connect(self.db_dsn)
            cur = conn.cursor()
            
            # Önce mevcut requirements'ları pasif yap (idempotency)
            cur.execute(f"""
                UPDATE {TABLE_NAME} 
                SET is_active = false 
                WHERE notice_id = %s
            """, (notice_id,))
            
            # Requirements'ları kategorize et ve kaydet
            requirement_mapping = {
                'room_requirements': 'room_block',
                'conference_requirements': 'conference',
                'av_requirements': 'av',
                'catering_requirements': 'catering',
                'compliance_requirements': 'compliance',
                'pricing_requirements': 'pricing',
                'general_requirements': 'general'
            }
            
            saved_count = 0
            
            for category, req_type in requirement_mapping.items():
                category_data = extracted_requirements.get(category, {})
                
                if isinstance(category_data, dict):
                    # Dictionary formatında requirements
                    for key, value in category_data.items():
                        if value is not None and value != '':
                            cur.execute(f"""
                                INSERT INTO {TABLE_NAME} 
                                (notice_id, requirement_type, requirement_category, 
                                 requirement_key, requirement_value, requirement_metadata, 
                                 extracted_by, is_active)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                            """, (
                                notice_id,
                                req_type,
                                category,
                                key,
                                json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                                json.dumps({'source': 'autogen_agent', 'extracted_at': datetime.now().isoformat()}),
                                extracted_by
                            ))
                            saved_count += 1
                
                elif isinstance(category_data, list):
                    # List formatında requirements
                    for idx, req_item in enumerate(category_data):
                        if isinstance(req_item, dict):
                            # Dict item
                            for key, value in req_item.items():
                                cur.execute(f"""
                                    INSERT INTO {TABLE_NAME} 
                                    (notice_id, requirement_type, requirement_category, 
                                     requirement_key, requirement_value, requirement_metadata, 
                                     extracted_by, is_active)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                                """, (
                                    notice_id,
                                    req_type,
                                    category,
                                    f"item_{idx}_{key}",
                                    json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                                    json.dumps({'source': 'autogen_agent', 'extracted_at': datetime.now().isoformat()}),
                                    extracted_by
                                ))
                                saved_count += 1
                        else:
                            # String item
                            cur.execute(f"""
                                INSERT INTO {TABLE_NAME} 
                                (notice_id, requirement_type, requirement_category, 
                                 requirement_key, requirement_value, requirement_metadata, 
                                 extracted_by, is_active)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                            """, (
                                notice_id,
                                req_type,
                                category,
                                f"item_{idx}",
                                str(req_item),
                                json.dumps({'source': 'autogen_agent', 'extracted_at': datetime.now().isoformat()}),
                                extracted_by
                            ))
                            saved_count += 1
            
            conn.commit()
            logger.info(f"✅ {saved_count} requirement kaydedildi: {notice_id}")
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Requirements kaydetme hatası: {e}")
            return False
    
    def get_requirements(self, notice_id: str, requirement_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Bir notice_id için requirements'ları getirir
        
        Args:
            notice_id: SAM.gov Notice ID
            requirement_type: Optional filter (room_block, av, catering, etc.)
            
        Returns:
            List of requirement dicts
        """
        try:
            conn = psycopg2.connect(self.db_dsn)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if requirement_type:
                cur.execute(f"""
                    SELECT * FROM {TABLE_NAME} 
                    WHERE notice_id = %s AND requirement_type = %s AND is_active = true
                    ORDER BY requirement_category, requirement_key
                """, (notice_id, requirement_type))
            else:
                cur.execute(f"""
                    SELECT * FROM {TABLE_NAME} 
                    WHERE notice_id = %s AND is_active = true
                    ORDER BY requirement_category, requirement_key
                """, (notice_id,))
            
            results = cur.fetchall()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"❌ Requirements getirme hatası: {e}")
            return []
    
    def compare_requirements(self, notice_id_1: str, notice_id_2: str) -> Dict[str, Any]:
        """
        İki notice_id'nin requirements'larını karşılaştırır (Compliance Matrix için)
        
        Args:
            notice_id_1: İlk notice ID
            notice_id_2: İkinci notice ID
            
        Returns:
            Comparison dict with matches, differences, etc.
        """
        try:
            reqs_1 = self.get_requirements(notice_id_1)
            reqs_2 = self.get_requirements(notice_id_2)
            
            # Compare logic
            comparison = {
                'notice_id_1': notice_id_1,
                'notice_id_2': notice_id_2,
                'reqs_1_count': len(reqs_1),
                'reqs_2_count': len(reqs_2),
                'matches': [],
                'differences': [],
                'missing_in_1': [],
                'missing_in_2': []
            }
            
            # Simple comparison (can be enhanced)
            reqs_1_keys = {(r['requirement_type'], r['requirement_key']) for r in reqs_1}
            reqs_2_keys = {(r['requirement_type'], r['requirement_key']) for r in reqs_2}
            
            comparison['matches'] = list(reqs_1_keys & reqs_2_keys)
            comparison['missing_in_1'] = list(reqs_2_keys - reqs_1_keys)
            comparison['missing_in_2'] = list(reqs_1_keys - reqs_2_keys)
            
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Requirements karşılaştırma hatası: {e}")
            return {}

if __name__ == "__main__":
    # Test
    manager = RequirementsManager()
    logger.info("Requirements Manager initialized")

