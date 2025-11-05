#!/usr/bin/env python3
"""Create RAG tables in Docker DB"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Docker DB
conn = psycopg2.connect(
    host='localhost',
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'sarlio41'),
    database=os.getenv('POSTGRES_DB', 'ZGR_AI')
)

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
    
    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id ON vector_chunks(document_id);")
    
    conn.commit()
    print("[OK] RAG tablolari olusturuldu!")

conn.close()









