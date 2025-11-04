#!/usr/bin/env python3
"""
Veritabanı şemasını kontrol et
"""

import sys
sys.path.append('.')
from streamlit_complete_with_mail import create_database_connection

def check_database_schema():
    conn = create_database_connection()
    if not conn:
        print("Veritabani baglantisi basarisiz!")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'opportunities' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print("Mevcut sutunlar:")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")
        
        # Eksik sütunları kontrol et
        existing_columns = [col[0] for col in columns]
        required_columns = ['solicitation_number', 'set_aside', 'response_deadline', 'estimated_value', 'place_of_performance']
        
        print("\nEksik sutunlar:")
        missing_columns = [col for col in required_columns if col not in existing_columns]
        for col in missing_columns:
            print(f"- {col}")
        
        if missing_columns:
            print("\nEksik sutunlari eklemek icin SQL:")
            for col in missing_columns:
                if col == 'solicitation_number':
                    print(f"ALTER TABLE opportunities ADD COLUMN {col} VARCHAR(255);")
                elif col == 'set_aside':
                    print(f"ALTER TABLE opportunities ADD COLUMN {col} VARCHAR(255);")
                elif col == 'response_deadline':
                    print(f"ALTER TABLE opportunities ADD COLUMN {col} TIMESTAMP;")
                elif col == 'estimated_value':
                    print(f"ALTER TABLE opportunities ADD COLUMN {col} DECIMAL(15,2);")
                elif col == 'place_of_performance':
                    print(f"ALTER TABLE opportunities ADD COLUMN {col} TEXT;")
        
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_schema()
