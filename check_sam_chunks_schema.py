#!/usr/bin/env python3
"""Check sam_chunks table schema"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host='localhost',
    database='ZGR_AI',
    user='postgres',
    password='sarlio41',
    port='5432'
)

cur = conn.cursor()

# List all tables with 'chunk' in name
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%chunk%'
    ORDER BY table_name;
""")
chunk_tables = cur.fetchall()

print("=" * 60)
print("CHUNK TABLES FOUND")
print("=" * 60)
for table in chunk_tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")
    
    # Get columns
    cur.execute(f"""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position;
    """)
    cols = cur.fetchall()
    
    print("  Columns:")
    for col in cols:
        col_name, data_type, max_len = col
        if max_len:
            print(f"    {col_name}: {data_type}({max_len})")
        else:
            print(f"    {col_name}: {data_type}")
    
    # Get count
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        print(f"  Total rows: {count:,}")
    except:
        print(f"  (Could not count rows)")
    
    # Check indexes
    cur.execute(f"""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = '{table_name}';
    """)
    indexes = cur.fetchall()
    if indexes:
        print(f"  Indexes ({len(indexes)}):")
        for idx in indexes:
            print(f"    - {idx[0]}")

conn.close()

