#!/usr/bin/env python3
"""
Check if notice_id 086008536ec84226ad9de043dc738d06 exists in database
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

NOTICE_ID = "086008536ec84226ad9de043dc738d06"

def check_notice_in_db():
    """Check if notice_id exists in all relevant database tables"""
    print(f"Checking {NOTICE_ID} in Database")
    print("=" * 60)
    
    # Database connection parameters
    db_host = os.getenv('DB_HOST', 'localhost')
    # Fix Docker hostname issue
    if db_host == 'db':
        db_host = 'localhost'
    
    db_params_list = [
        {
            'host': db_host,
            'database': 'ZGR_AI',  # For sow_analysis, knowledge_facts
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'sarlio41'),
            'port': os.getenv('DB_PORT', '5432')
        },
        {
            'host': db_host,
            'database': os.getenv('DB_NAME', 'sam'),  # For opportunities, hotel_opportunities_new
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'sarlio41'),
            'port': os.getenv('DB_PORT', '5432')
        }
    ]
    
    found_anywhere = False
    
    # ===== CHECK 1: opportunities table in 'sam' database =====
    print(f"\n[1] Checking opportunities table in 'sam' database...")
    conn_sam = None
    try:
        conn_sam = psycopg2.connect(**db_params_list[1])
        print("[SUCCESS] Connected to SAM database")
        
        with conn_sam.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    id, 
                    opportunity_id, 
                    title, 
                    description, 
                    posted_date, 
                    naics_code, 
                    contract_type, 
                    organization_type,
                    cached_data,
                    cache_updated_at
                FROM opportunities 
                WHERE opportunity_id = %s
            """, (NOTICE_ID,))
            
            opportunity = cursor.fetchone()
            
            if opportunity:
                found_anywhere = True
                print("[FOUND] Opportunity found in opportunities table!")
                print(f"  - ID: {opportunity['id']}")
                print(f"  - Title: {opportunity['title'] or 'N/A'}")
                if opportunity['description']:
                    print(f"  - Description: {opportunity['description'][:100]}...")
                print(f"  - Posted Date: {opportunity['posted_date']}")
                print(f"  - NAICS Code: {opportunity['naics_code']}")
                print(f"  - Contract Type: {opportunity['contract_type']}")
                print(f"  - Organization: {opportunity['organization_type']}")
                if opportunity['cached_data']:
                    print(f"  - Cached Data: [YES] Available")
                    print(f"  - Cache Updated: {opportunity['cache_updated_at']}")
                else:
                    print(f"  - Cached Data: [NO] None")
            else:
                print("[NOT FOUND] Opportunity not in opportunities table")
    except Exception as e:
        print(f"[ERROR] SAM database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn_sam:
            conn_sam.close()
    
    # ===== CHECK 2: hotel_opportunities_new table =====
    print(f"\n[2] Checking hotel_opportunities_new table...")
    try:
        conn_sam = psycopg2.connect(**db_params_list[1])
        with conn_sam.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    notice_id,
                    title,
                    agency,
                    posted_date,
                    naics_code
                FROM hotel_opportunities_new 
                WHERE notice_id = %s
            """, (NOTICE_ID,))
            
            hotel_opp = cursor.fetchone()
            
            if hotel_opp:
                found_anywhere = True
                print("[FOUND] Found in hotel_opportunities_new table!")
                print(f"  - Notice ID: {hotel_opp['notice_id']}")
                print(f"  - Title: {hotel_opp['title'] or 'N/A'}")
                print(f"  - Agency: {hotel_opp['agency'] or 'N/A'}")
                print(f"  - Posted Date: {hotel_opp['posted_date']}")
                print(f"  - NAICS Code: {hotel_opp['naics_code']}")
            else:
                print("[NOT FOUND] Not in hotel_opportunities_new table")
    except Exception as e:
        print(f"[ERROR] hotel_opportunities_new check error: {e}")
    finally:
        if conn_sam:
            conn_sam.close()
    
    # ===== CHECK 3: sow_analysis table in 'ZGR_AI' database =====
    print(f"\n[3] Checking sow_analysis table in 'ZGR_AI' database...")
    conn_zgr = None
    try:
        conn_zgr = psycopg2.connect(**db_params_list[0])
        print("[SUCCESS] Connected to ZGR_AI database")
        
        with conn_zgr.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    analysis_id,
                    notice_id,
                    template_version,
                    sow_payload,
                    source_docs,
                    is_active,
                    created_at,
                    updated_at
                FROM sow_analysis 
                WHERE notice_id = %s
                ORDER BY updated_at DESC
            """, (NOTICE_ID,))
            
            sow_analyses = cursor.fetchall()
            
            if sow_analyses:
                found_anywhere = True
                print(f"[FOUND] Found {len(sow_analyses)} SOW analysis(es)!")
                
                for i, analysis in enumerate(sow_analyses, 1):
                    print(f"\n  Analysis {i}:")
                    print(f"    - Analysis ID: {analysis['analysis_id']}")
                    print(f"    - Template Version: {analysis['template_version']}")
                    print(f"    - Is Active: {analysis['is_active']}")
                    print(f"    - Created: {analysis['created_at']}")
                    print(f"    - Updated: {analysis['updated_at']}")
                    
                    if analysis['sow_payload']:
                        payload = analysis['sow_payload']
                        if isinstance(payload, dict):
                            print(f"    - SOW Payload Keys: {list(payload.keys())}")
            else:
                print("[NOT FOUND] No SOW analysis found")
            
            # Check vw_active_sow view
            cursor.execute("""
                SELECT 
                    notice_id,
                    template_version,
                    sow_payload,
                    created_at,
                    updated_at
                FROM vw_active_sow 
                WHERE notice_id = %s
            """, (NOTICE_ID,))
            
            active_sow = cursor.fetchone()
            
            if active_sow:
                print("[FOUND] Also found in vw_active_sow view!")
            else:
                print("[NOT FOUND] Not in vw_active_sow view")
                
    except Exception as e:
        print(f"[ERROR] ZGR_AI database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn_zgr:
            conn_zgr.close()
    
    # ===== CHECK 4: knowledge_facts table =====
    print(f"\n[4] Checking knowledge_facts table...")
    try:
        conn_zgr = psycopg2.connect(**db_params_list[0])
        with conn_zgr.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    notice_id,
                    schema_version,
                    payload,
                    source_docs,
                    created_at,
                    updated_at
                FROM knowledge_facts 
                WHERE notice_id = %s
                ORDER BY updated_at DESC
            """, (NOTICE_ID,))
            
            knowledge_records = cursor.fetchall()
            
            if knowledge_records:
                found_anywhere = True
                print(f"[FOUND] Found {len(knowledge_records)} knowledge fact(s)!")
                for i, record in enumerate(knowledge_records, 1):
                    print(f"\n  Record {i}:")
                    print(f"    - ID: {record['id']}")
                    print(f"    - Schema Version: {record['schema_version']}")
                    print(f"    - Created: {record['created_at']}")
            else:
                print("[NOT FOUND] No knowledge facts found")
    except Exception as e:
        print(f"[ERROR] knowledge_facts check error: {e}")
    finally:
        if conn_zgr:
            conn_zgr.close()
    
    # ===== SUMMARY =====
    print("\n" + "=" * 60)
    if found_anywhere:
        print(f"[YES] SUMMARY: {NOTICE_ID} EXISTS in database!")
        print("   The notice is present in at least one table.")
        print("   You can use the database data instead of calling SAM API.")
    else:
        print(f"[NO] SUMMARY: {NOTICE_ID} NOT FOUND in database!")
        print("   The notice is not in any table.")
        print("   You need to fetch it from SAM API (but rate limit is blocking).")

if __name__ == "__main__":
    check_notice_in_db()

