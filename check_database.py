#!/usr/bin/env python3
"""
Database Structure Check
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_database_structure():
    """Veritabanı yapısını kontrol et"""
    
    print("=== DATABASE STRUCTURE CHECK ===")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "sam"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "sarlio41")
        )
        
        cursor = conn.cursor()
        
        # Tabloları listele
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        
        tables = cursor.fetchall()
        print(f"Mevcut tablolar: {[table[0] for table in tables]}")
        
        # Opportunities tablosu varsa yapısını göster
        if any('opportunities' in table for table in tables):
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'opportunities'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print(f"\nOpportunities tablosu kolonlari:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]}")
        else:
            print("Opportunities tablosu bulunamadi")
        
        conn.close()
        
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    check_database_structure()

















