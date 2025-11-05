#!/usr/bin/env python3
"""
Requirements Tablosu Oluşturma
Kritik gereksinimleri yapılandırılmış olarak saklar
"""

import os
import psycopg2
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432")

def create_requirements_table():
    """Requirements tablosunu oluşturur"""
    try:
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        # MergenAI requirements tablosu (structured_requirements)
        table_name = 'structured_requirements'
        
        # Önce tablo var mı kontrol et
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table_name}'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            logger.info(f"ℹ️ {table_name} tablosu zaten mevcut")
        else:
            # Structured requirements tablosu oluştur
            cur.execute(f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    notice_id VARCHAR(255) NOT NULL,
                    requirement_type VARCHAR(50) NOT NULL,
                    requirement_category VARCHAR(100),
                    requirement_key VARCHAR(255),
                    requirement_value TEXT,
                    requirement_metadata JSONB,
                    extracted_at TIMESTAMP DEFAULT NOW(),
                    extracted_by VARCHAR(50) DEFAULT 'autogen_agent',
                    is_active BOOLEAN DEFAULT true
                );
            """)
            conn.commit()
            logger.info(f"✅ {table_name} tablosu oluşturuldu")
        
        # Indexes (her durumda oluştur)
        try:
            # Önce sütunları kontrol et
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}';
            """)
            existing_columns = [row[0] for row in cur.fetchall()]
            
            if 'notice_id' in existing_columns:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_notice_id ON {table_name}(notice_id);")
            if 'requirement_type' in existing_columns:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_type ON {table_name}(requirement_type);")
            if 'requirement_category' in existing_columns:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_category ON {table_name}(requirement_category);")
            if 'is_active' in existing_columns:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_active ON {table_name}(is_active);")
            if 'requirement_metadata' in existing_columns:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_metadata ON {table_name} USING GIN(requirement_metadata);")
            
            conn.commit()
            logger.info("✅ Indexes oluşturuldu/güncellendi")
        except Exception as idx_error:
            conn.rollback()
            logger.warning(f"⚠️ Index oluşturma hatası (non-critical): {idx_error}")
        
        # Tablo yapısını göster
        try:
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            if columns:
                logger.info("📋 Tablo Yapısı:")
                for col in columns:
                    logger.info(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                logger.warning("⚠️ Tablo yapısı alınamadı")
        except Exception as e:
            logger.warning(f"⚠️ Tablo yapısı gösterilemedi: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Hata: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def add_embedding_version_column():
    """sam_chunks tablosuna embedding_model_version sütunu ekler"""
    try:
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        
        # Önce hangi chunk tabloları var kontrol et
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%chunk%' OR table_name = 'hotel_chunks')
            ORDER BY table_name;
        """)
        
        chunk_tables = [r[0] for r in cur.fetchall()]
        logger.info(f"📋 Bulunan chunk tabloları: {chunk_tables}")
        
        # İlk chunk tablosuna embedding versiyonlama ekle
        if chunk_tables:
            target_table = chunk_tables[0]  # İlk chunk tablosu
            logger.info(f"📊 Embedding versiyonlama eklenecek tablo: {target_table}")
            
            # Sütun var mı kontrol et
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{target_table}' AND column_name = 'embedding_model_version';
            """)
            
            if cur.fetchone():
                logger.info(f"✅ {target_table}.embedding_model_version sütunu zaten mevcut")
            else:
                # Sütunu ekle
                cur.execute(f"""
                    ALTER TABLE {target_table} 
                    ADD COLUMN embedding_model_version VARCHAR(50) DEFAULT 'sentence-transformers/all-MiniLM-L6-v2';
                """)
                
                # Mevcut embedding'leri versiyonla işaretle
                cur.execute(f"""
                    UPDATE {target_table} 
                    SET embedding_model_version = 'sentence-transformers/all-MiniLM-L6-v2'
                    WHERE embedding IS NOT NULL AND embedding_model_version IS NULL;
                """)
                
                # Index ekle
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{target_table}_embedding_version 
                    ON {target_table}(embedding_model_version);
                """)
                
                conn.commit()
                logger.info(f"✅ {target_table}.embedding_model_version sütunu başarıyla eklendi")
        else:
            logger.warning("⚠️ Chunk tablosu bulunamadı - embedding versiyonlama atlandı")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("MERGENAI - Requirements Tablosu ve Embedding Versiyonlama")
    logger.info("=" * 60)
    
    # 1. Requirements tablosu oluştur
    logger.info("\n[1/2] Requirements tablosu oluşturuluyor...")
    if create_requirements_table():
        logger.info("✅ Requirements tablosu hazır")
    else:
        logger.error("❌ Requirements tablosu oluşturulamadı")
    
    # 2. Embedding versiyonlama sütunu ekle
    logger.info("\n[2/2] Embedding versiyonlama sütunu ekleniyor...")
    if add_embedding_version_column():
        logger.info("✅ Embedding versiyonlama hazır")
    else:
        logger.error("❌ Embedding versiyonlama eklenemedi")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Tüm değişiklikler tamamlandı!")
    logger.info("=" * 60)

