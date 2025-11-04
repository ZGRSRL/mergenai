#!/usr/bin/env python3
"""
Check 70LART26QPFB00001 in local database
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

def check_opportunity_in_db():
    """Check if 70LART26QPFB00001 exists in local database"""
    print("Checking 70LART26QPFB00001 in Local Database")
    print("=" * 50)
    
    # Database connection parameters - try both databases
    db_params_list = [
        {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': 'ZGR_AI',  # For sow_analysis table
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'sarlio41'),
            'port': os.getenv('DB_PORT', '5432')
        },
        {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'sam'),  # For opportunities table
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'sarlio41'),
            'port': os.getenv('DB_PORT', '5432')
        }
    ]
    
    # Check opportunities table in 'sam' database
    print(f"Connecting to SAM database for opportunities...")
    conn_sam = None
    try:
        conn_sam = psycopg2.connect(**db_params_list[1])
        print("[SUCCESS] SAM database connected!")
        
        with conn_sam.cursor(cursor_factory=RealDictCursor) as cursor:
            print(f"\n[CHECK] Looking in opportunities table...")
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
            """, ("70LART26QPFB00001",))
            
            opportunity = cursor.fetchone()
            
            if opportunity:
                print("[SUCCESS] Opportunity found in opportunities table!")
                print(f"  - ID: {opportunity['id']}")
                print(f"  - Title: {opportunity['title']}")
                print(f"  - Description: {opportunity['description'][:100]}...")
                print(f"  - Posted Date: {opportunity['posted_date']}")
                print(f"  - NAICS Code: {opportunity['naics_code']}")
                print(f"  - Contract Type: {opportunity['contract_type']}")
                print(f"  - Organization: {opportunity['organization_type']}")
                
                if opportunity['cached_data']:
                    print(f"  - Cached Data: Available")
                    print(f"  - Cache Updated: {opportunity['cache_updated_at']}")
                else:
                    print(f"  - Cached Data: None")
            else:
                print("[WARNING] Opportunity not found in opportunities table")
    except Exception as e:
        print(f"[ERROR] SAM database error: {e}")
    finally:
        if conn_sam:
            conn_sam.close()
    
    # Check sow_analysis table in 'ZGR_AI' database
    print(f"\nConnecting to ZGR_AI database for SOW analysis...")
    conn_zgr = None
    try:
        conn_zgr = psycopg2.connect(**db_params_list[0])
        print("[SUCCESS] ZGR_AI database connected!")
        
        with conn_zgr.cursor(cursor_factory=RealDictCursor) as cursor:
            
            # Check sow_analysis table
            print(f"\n[CHECK] Looking in sow_analysis table...")
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
            """, ("70LART26QPFB00001",))
            
            sow_analyses = cursor.fetchall()
            
            if sow_analyses:
                print(f"[SUCCESS] Found {len(sow_analyses)} SOW analysis(es)!")
                
                for i, analysis in enumerate(sow_analyses, 1):
                    print(f"\n  Analysis {i}:")
                    print(f"    - Analysis ID: {analysis['analysis_id']}")
                    print(f"    - Template Version: {analysis['template_version']}")
                    print(f"    - Is Active: {analysis['is_active']}")
                    print(f"    - Created: {analysis['created_at']}")
                    print(f"    - Updated: {analysis['updated_at']}")
                    
                    # Check SOW payload
                    if analysis['sow_payload']:
                        payload = analysis['sow_payload']
                        print(f"    - SOW Payload Keys: {list(payload.keys()) if isinstance(payload, dict) else 'Not a dict'}")
                        
                        # Show some key fields
                        if isinstance(payload, dict):
                            if 'period_of_performance' in payload:
                                print(f"      * Period: {payload['period_of_performance']}")
                            if 'room_block' in payload:
                                room_block = payload['room_block']
                                if isinstance(room_block, dict):
                                    print(f"      * Room Block: {room_block.get('total_rooms_per_night', 'N/A')} rooms")
                            if 'function_space' in payload:
                                func_space = payload['function_space']
                                if isinstance(func_space, dict):
                                    print(f"      * General Session: {func_space.get('general_session', {}).get('capacity', 'N/A')} capacity")
                    else:
                        print(f"    - SOW Payload: None")
                    
                    # Check source docs
                    if analysis['source_docs']:
                        source_docs = analysis['source_docs']
                        print(f"    - Source Docs: {source_docs}")
                    else:
                        print(f"    - Source Docs: None")
            else:
                print("[WARNING] No SOW analysis found")
            
            # Check vw_active_sow view
            print(f"\n[CHECK] Looking in vw_active_sow view...")
            cursor.execute("""
                SELECT 
                    notice_id,
                    template_version,
                    sow_payload,
                    created_at,
                    updated_at
                FROM vw_active_sow 
                WHERE notice_id = %s
            """, ("70LART26QPFB00001",))
            
            active_sow = cursor.fetchone()
            
            if active_sow:
                print("[SUCCESS] Found in vw_active_sow view!")
                print(f"  - Template Version: {active_sow['template_version']}")
                print(f"  - Updated: {active_sow['updated_at']}")
            else:
                print("[WARNING] Not found in vw_active_sow view")
                
    except Exception as e:
        print(f"[ERROR] ZGR_AI database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn_zgr:
            conn_zgr.close()

def main():
    """Main function"""
    check_opportunity_in_db()

if __name__ == "__main__":
    main()
