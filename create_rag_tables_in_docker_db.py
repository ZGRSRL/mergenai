#!/usr/bin/env python3
"""Create RAG tables in Docker DB (inside container)"""
import psycopg2

# Connect to Docker DB from inside container (host='db')
try:
    # Try Docker internal connection first
    conn = psycopg2.connect(
        host='db',
        port=5432,
        user='postgres',
        password='sarlio41',
        database='ZGR_AI'
    )
    print("[OK] Docker internal connection (host=db)")
except:
    # Fallback to localhost
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='sarlio41',
        database='ZGR_AI'
    )
    print("[OK] Localhost connection")

with conn.cursor() as cur:
    # Create documents table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            kind VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            path VARCHAR(500) NOT NULL,
            meta_json JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("[OK] documents table")
    
    # Create vector_chunks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vector_chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk TEXT NOT NULL,
            embedding JSONB,
            chunk_type VARCHAR(50),
            page_number INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("[OK] vector_chunks table")
    
    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id ON vector_chunks(document_id);")
    print("[OK] indexes")
    
    conn.commit()
    print("\n[SUCCESS] RAG tablolari olusturuldu!")

conn.close()









