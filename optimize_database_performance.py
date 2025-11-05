#!/usr/bin/env python3
"""
Database Performance Optimization Script
- Migrate from IVFFlat to HNSW index
- Unify chunk tables (sam_chunks, vector_chunks) into single table
- Add source_type column for better organization
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database performance optimization manager"""
    
    def __init__(self, db_name: str = 'ZGR_AI'):
        """Initialize optimizer"""
        self.db_name = db_name
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost').replace('db', 'localhost'),
            'database': db_name,
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'sarlio41'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info(f"Connected to {self.db_name}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def check_current_indexes(self) -> List[Dict[str, Any]]:
        """Check current vector indexes"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check for pgvector extension
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'vector'
                    ) as has_extension;
                """)
                has_extension = cur.fetchone()['has_extension']
                
                if not has_extension:
                    logger.warning("pgvector extension not installed")
                    return []
                
                # Check indexes on sam_chunks
                cur.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE tablename = 'sam_chunks'
                    AND indexdef LIKE '%vector%' OR indexdef LIKE '%ivfflat%' OR indexdef LIKE '%hnsw%';
                """)
                
                indexes = cur.fetchall()
                logger.info(f"Found {len(indexes)} vector-related indexes")
                return [dict(idx) for idx in indexes]
                
        except Exception as e:
            logger.error(f"Error checking indexes: {e}")
            return []
    
    def migrate_to_hnsw(self, drop_old: bool = True):
        """
        Migrate from IVFFlat to HNSW index
        
        Args:
            drop_old: Drop old IVFFlat index if exists
        """
        try:
            with self.conn.cursor() as cur:
                # 1. Enable pgvector extension
                logger.info("Enabling pgvector extension...")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.conn.commit()
                logger.info("✓ pgvector extension enabled")
                
                # 2. Check if sam_chunks table exists and has embedding column
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'sam_chunks' 
                    AND column_name = 'embedding';
                """)
                embedding_col = cur.fetchone()
                
                if not embedding_col:
                    logger.error("sam_chunks.embedding column not found!")
                    return False
                
                logger.info(f"Found embedding column: {embedding_col[1]}")
                
                # 3. Check if embedding is vector type or JSONB
                if embedding_col[1] == 'jsonb':
                    logger.info("Converting JSONB embeddings to vector type...")
                    # First, check if we have vector column
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'sam_chunks' 
                        AND column_name = 'embedding_vector';
                    """)
                    has_vector_col = cur.fetchone()
                    
                    if not has_vector_col:
                        # Add vector column
                        cur.execute("""
                            ALTER TABLE sam_chunks 
                            ADD COLUMN embedding_vector vector(384);
                        """)
                        logger.info("✓ Added embedding_vector column")
                    
                    # Convert JSONB to vector (sample conversion - adjust dimension as needed)
                    cur.execute("""
                        UPDATE sam_chunks 
                        SET embedding_vector = (
                            SELECT vector(ARRAY(
                                SELECT jsonb_array_elements_text(embedding::jsonb)
                            )::float[])
                        )
                        WHERE embedding IS NOT NULL 
                        AND embedding_vector IS NULL
                        LIMIT 1000;
                    """)
                    self.conn.commit()
                    logger.info("✓ Converted first 1000 embeddings (test)")
                    
                # 4. Drop old IVFFlat index if exists
                if drop_old:
                    logger.info("Dropping old IVFFlat indexes...")
                    cur.execute("""
                        DROP INDEX IF EXISTS sam_chunks_embedding_idx;
                        DROP INDEX IF EXISTS idx_sam_chunks_embedding_ivfflat;
                    """)
                    self.conn.commit()
                    logger.info("✓ Old indexes dropped")
                
                # 5. Create HNSW index
                logger.info("Creating HNSW index...")
                # HNSW parameters: m=16 (connections per layer), ef_construction=64 (search quality)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sam_chunks_embedding_hnsw 
                    ON sam_chunks 
                    USING hnsw (embedding_vector vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """)
                self.conn.commit()
                logger.info("✓ HNSW index created successfully")
                
                return True
                
        except Exception as e:
            logger.error(f"Error migrating to HNSW: {e}")
            self.conn.rollback()
            return False
    
    def unify_chunk_tables(self):
        """
        Unify sam_chunks and vector_chunks into single unified_chunks table
        with source_type column
        """
        try:
            with self.conn.cursor() as cur:
                # 1. Create unified_chunks table
                logger.info("Creating unified_chunks table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS unified_chunks (
                        id SERIAL PRIMARY KEY,
                        chunk_text TEXT NOT NULL,
                        embedding_vector vector(384),
                        embedding_jsonb JSONB,  -- Keep JSONB for compatibility
                        source_type VARCHAR(50) NOT NULL,  -- 'hotel_title', 'hotel_description', 'hotel_document', 'sam_document', etc.
                        source_id VARCHAR(255),  -- notice_id, document_id, etc.
                        chunk_type VARCHAR(50),  -- 'title', 'description', 'document', etc.
                        opportunity_id VARCHAR(255),
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # 2. Create indexes
                logger.info("Creating indexes on unified_chunks...")
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_unified_chunks_source_type 
                    ON unified_chunks(source_type);
                    
                    CREATE INDEX IF NOT EXISTS idx_unified_chunks_opportunity_id 
                    ON unified_chunks(opportunity_id);
                    
                    CREATE INDEX IF NOT EXISTS idx_unified_chunks_source_id 
                    ON unified_chunks(source_id);
                """)
                
                # 3. Create HNSW index on unified_chunks
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_unified_chunks_embedding_hnsw 
                    ON unified_chunks 
                    USING hnsw (embedding_vector vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """)
                
                self.conn.commit()
                logger.info("✓ unified_chunks table created")
                
                # 4. Migrate data from sam_chunks
                logger.info("Migrating data from sam_chunks...")
                cur.execute("""
                    INSERT INTO unified_chunks (
                        chunk_text, embedding_vector, embedding_jsonb,
                        source_type, source_id, chunk_type, opportunity_id, metadata, created_at
                    )
                    SELECT 
                        content as chunk_text,
                        embedding_vector,
                        embedding::jsonb as embedding_jsonb,
                        CASE 
                            WHEN chunk_type = 'title' THEN 'hotel_title'
                            WHEN chunk_type = 'description' THEN 'hotel_description'
                            WHEN chunk_type = 'document' THEN 'hotel_document'
                            ELSE 'hotel_unknown'
                        END as source_type,
                        opportunity_id as source_id,
                        chunk_type,
                        opportunity_id,
                        jsonb_build_object(
                            'chunk_id', chunk_id,
                            'chunk_type', chunk_type,
                            'original_table', 'sam_chunks'
                        ) as metadata,
                        created_at
                    FROM sam_chunks
                    WHERE NOT EXISTS (
                        SELECT 1 FROM unified_chunks 
                        WHERE unified_chunks.source_id = sam_chunks.opportunity_id
                        AND unified_chunks.chunk_type = sam_chunks.chunk_type
                        AND unified_chunks.chunk_text = sam_chunks.content
                    );
                """)
                
                migrated_count = cur.rowcount
                self.conn.commit()
                logger.info(f"✓ Migrated {migrated_count:,} chunks from sam_chunks")
                
                # 5. Migrate from vector_chunks if exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'vector_chunks'
                    ) as table_exists;
                """)
                has_vector_chunks = cur.fetchone()[0]
                
                if has_vector_chunks:
                    logger.info("Migrating data from vector_chunks...")
                    cur.execute("""
                        INSERT INTO unified_chunks (
                            chunk_text, embedding_vector, embedding_jsonb,
                            source_type, source_id, chunk_type, metadata, created_at
                        )
                        SELECT 
                            chunk as chunk_text,
                            embedding::vector as embedding_vector,
                            embedding::jsonb as embedding_jsonb,
                            'sam_document' as source_type,
                            document_id::text as source_id,
                            chunk_type,
                            jsonb_build_object(
                                'document_id', document_id,
                                'page_number', page_number,
                                'original_table', 'vector_chunks'
                            ) as metadata,
                            created_at
                        FROM vector_chunks
                        WHERE NOT EXISTS (
                            SELECT 1 FROM unified_chunks 
                            WHERE unified_chunks.source_id = vector_chunks.document_id::text
                            AND unified_chunks.chunk_text = vector_chunks.chunk
                        );
                    """)
                    
                    migrated_count = cur.rowcount
                    self.conn.commit()
                    logger.info(f"✓ Migrated {migrated_count:,} chunks from vector_chunks")
                
                return True
                
        except Exception as e:
            logger.error(f"Error unifying chunk tables: {e}")
            self.conn.rollback()
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                stats = {}
                
                # Count chunks in each table
                for table in ['sam_chunks', 'vector_chunks', 'unified_chunks']:
                    cur.execute(f"""
                        SELECT COUNT(*) as count 
                        FROM {table}
                        WHERE EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        );
                    """)
                    result = cur.fetchone()
                    if result:
                        stats[f'{table}_count'] = result['count']
                
                # Check index sizes
                cur.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes
                    WHERE tablename IN ('sam_chunks', 'unified_chunks')
                    AND indexrelid::regclass::text LIKE '%hnsw%' OR indexrelid::regclass::text LIKE '%ivfflat%';
                """)
                indexes = cur.fetchall()
                stats['indexes'] = [dict(idx) for idx in indexes]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
            logger.info("Connection closed")


def main():
    """Main optimization workflow"""
    print("=" * 80)
    print("DATABASE PERFORMANCE OPTIMIZATION")
    print("=" * 80)
    print("\nOptimizations:")
    print("1. Migrate IVFFlat → HNSW index (10-20% faster searches)")
    print("2. Unify chunk tables (sam_chunks + vector_chunks → unified_chunks)")
    print("3. Add source_type column for better organization")
    print("\n" + "=" * 80)
    
    optimizer = DatabaseOptimizer(db_name='ZGR_AI')
    
    if not optimizer.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Step 1: Check current state
        print("\n[STEP 1] Checking current indexes...")
        indexes = optimizer.check_current_indexes()
        print(f"Found {len(indexes)} vector indexes")
        for idx in indexes:
            print(f"  - {idx.get('indexname', 'N/A')}")
        
        # Step 2: Migrate to HNSW
        print("\n[STEP 2] Migrating to HNSW index...")
        response = input("Continue with HNSW migration? (y/n): ")
        if response.lower() == 'y':
            success = optimizer.migrate_to_hnsw(drop_old=True)
            if success:
                print("✅ HNSW migration completed")
            else:
                print("❌ HNSW migration failed")
        else:
            print("⏭️  Skipped HNSW migration")
        
        # Step 3: Unify chunk tables
        print("\n[STEP 3] Unifying chunk tables...")
        response = input("Continue with chunk table unification? (y/n): ")
        if response.lower() == 'y':
            success = optimizer.unify_chunk_tables()
            if success:
                print("✅ Chunk unification completed")
            else:
                print("❌ Chunk unification failed")
        else:
            print("⏭️  Skipped chunk unification")
        
        # Step 4: Statistics
        print("\n[STEP 4] Final statistics...")
        stats = optimizer.get_statistics()
        print("\nChunk counts:")
        for key, value in stats.items():
            if 'count' in key:
                print(f"  {key}: {value:,}")
        
        print("\nIndex sizes:")
        for idx in stats.get('indexes', []):
            print(f"  {idx.get('indexname', 'N/A')}: {idx.get('index_size', 'N/A')}")
        
        print("\n" + "=" * 80)
        print("✅ Optimization complete!")
        print("=" * 80)
        
    finally:
        optimizer.close()


if __name__ == "__main__":
    main()

