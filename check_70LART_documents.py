#!/usr/bin/env python3
"""
Check if 70LART26QPFB00001 documents are downloaded
"""

import os
import sys
import json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Load environment variables
load_dotenv()

def check_downloaded_documents():
    """Check if documents are downloaded for 70LART26QPFB00001"""
    print("Checking 70LART26QPFB00001 Documents")
    print("=" * 50)
    
    # Database connection
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'sam',  # opportunities table is in sam database
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'sarlio41'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        print("[SUCCESS] Connected to SAM database")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get opportunity data
            cursor.execute("""
                SELECT 
                    opportunity_id,
                    title,
                    cached_data,
                    cache_updated_at
                FROM opportunities 
                WHERE opportunity_id = %s
            """, ("70LART26QPFB00001",))
            
            opportunity = cursor.fetchone()
            
            if not opportunity:
                print("[ERROR] Opportunity not found in database")
                return
            
            print(f"[INFO] Opportunity: {opportunity['title']}")
            print(f"[INFO] Cache Updated: {opportunity['cache_updated_at']}")
            
            # Check cached_data
            cached_data = opportunity.get('cached_data')
            if not cached_data:
                print("[WARNING] No cached data found")
                return
            
            print(f"\n[CHECK] Analyzing cached data...")
            
            # Parse cached data
            if isinstance(cached_data, str):
                try:
                    cached_data = json.loads(cached_data)
                except json.JSONDecodeError:
                    print("[ERROR] Cached data is not valid JSON")
                    return
            
            print(f"[SUCCESS] Cached data loaded")
            print(f"  - Type: {type(cached_data)}")
            print(f"  - Keys: {list(cached_data.keys()) if isinstance(cached_data, dict) else 'Not a dict'}")
            
            # Look for resource links in cached data
            resource_links = None
            if isinstance(cached_data, dict):
                # Check different possible locations for resource links
                resource_links = (
                    cached_data.get('resourceLinks') or
                    cached_data.get('resource_links') or
                    cached_data.get('attachments') or
                    cached_data.get('documents')
                )
            
            if resource_links:
                print(f"\n[SUCCESS] Found resource links in cached data!")
                print(f"  - Count: {len(resource_links) if isinstance(resource_links, list) else 'Not a list'}")
                
                if isinstance(resource_links, list):
                    for i, link in enumerate(resource_links, 1):
                        print(f"\n  Document {i}:")
                        if isinstance(link, dict):
                            print(f"    - Filename: {link.get('filename', 'Unknown')}")
                            print(f"    - URL: {link.get('url', 'No URL')}")
                            print(f"    - Type: {link.get('type', 'Unknown')}")
                            print(f"    - Size: {link.get('size', 'Unknown')}")
                        else:
                            print(f"    - Raw: {link}")
            else:
                print("[WARNING] No resource links found in cached data")
                print("  - Checking for other document references...")
                
                # Look for any document-related fields
                doc_fields = []
                if isinstance(cached_data, dict):
                    for key, value in cached_data.items():
                        if any(word in key.lower() for word in ['doc', 'attach', 'file', 'pdf', 'link']):
                            doc_fields.append(f"{key}: {value}")
                
                if doc_fields:
                    print("  - Found document-related fields:")
                    for field in doc_fields:
                        print(f"    * {field}")
                else:
                    print("  - No document-related fields found")
            
            # Check for downloaded files in common directories
            print(f"\n[CHECK] Looking for downloaded files...")
            
            download_dirs = [
                "downloads",
                "sam_downloads", 
                "downloads_70LART",
                "workflow_downloads_70LART",
                "test_downloads",
                "attachments",
                "documents"
            ]
            
            found_files = []
            for dir_name in download_dirs:
                if os.path.exists(dir_name):
                    print(f"  - Checking directory: {dir_name}")
                    for file_path in Path(dir_name).rglob("*"):
                        if file_path.is_file():
                            # Check if filename contains 70LART or FLETC
                            filename = file_path.name.lower()
                            if any(keyword in filename for keyword in ['70lart', 'fletc', 'artesia', 'lodging']):
                                found_files.append(str(file_path))
                                print(f"    * Found: {file_path}")
                else:
                    print(f"  - Directory not found: {dir_name}")
            
            if found_files:
                print(f"\n[SUCCESS] Found {len(found_files)} downloaded files!")
                for file_path in found_files:
                    file_size = os.path.getsize(file_path)
                    print(f"  - {file_path} ({file_size} bytes)")
            else:
                print(f"\n[WARNING] No downloaded files found")
            
            # Check SOW analysis for source documents
            print(f"\n[CHECK] Checking SOW analysis for source documents...")
            
            # Connect to ZGR_AI database for SOW analysis
            zgr_params = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': 'ZGR_AI',
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'sarlio41'),
                'port': os.getenv('DB_PORT', '5432')
            }
            
            try:
                zgr_conn = psycopg2.connect(**zgr_params)
                with zgr_conn.cursor(cursor_factory=RealDictCursor) as zgr_cursor:
                    zgr_cursor.execute("""
                        SELECT 
                            source_docs,
                            sow_payload
                        FROM sow_analysis 
                        WHERE notice_id = %s
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, ("70LART26QPFB00001",))
                    
                    sow_data = zgr_cursor.fetchone()
                    
                    if sow_data and sow_data['source_docs']:
                        source_docs = sow_data['source_docs']
                        print(f"[SUCCESS] Found source documents in SOW analysis!")
                        print(f"  - Source Docs: {source_docs}")
                        
                        if isinstance(source_docs, dict):
                            doc_ids = source_docs.get('doc_ids', [])
                            urls = source_docs.get('urls', [])
                            sha256 = source_docs.get('sha256', [])
                            
                            print(f"  - Document IDs: {doc_ids}")
                            print(f"  - URLs: {urls}")
                            print(f"  - SHA256: {sha256}")
                    else:
                        print("[WARNING] No source documents in SOW analysis")
                        
            except Exception as e:
                print(f"[ERROR] Could not check SOW analysis: {e}")
            finally:
                if 'zgr_conn' in locals():
                    zgr_conn.close()
            
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def main():
    """Main function"""
    check_downloaded_documents()

if __name__ == "__main__":
    main()













