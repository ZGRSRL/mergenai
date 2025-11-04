#!/usr/bin/env python3
"""
Eksik sütunları veritabanına ekle
"""

import sys
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection

def add_missing_columns():
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglantisi basarisiz!")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Eksik sütunları ekle
        columns_to_add = [
            "ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS solicitation_number VARCHAR(255);",
            "ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS response_deadline TIMESTAMP;",
            "ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS estimated_value DECIMAL(15,2);"
        ]
        
        for sql in columns_to_add:
            print(f"Calistiriliyor: {sql}")
            cursor.execute(sql)
        
        conn.commit()
        print("Eksik sutunlar basariyla eklendi!")
        return True
        
    except Exception as e:
        print(f"Hata: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_columns()
