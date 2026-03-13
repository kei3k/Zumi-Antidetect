import sqlite3
import os

db_path = r"D:\K\CHAPALL\Chapall.dist\chapall.db"

def check_db():
    if not os.path.exists(db_path):
        print(f"File not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lay danh sach bang
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in DB: {tables}")
        
        for table in tables:
            t_name = table[0]
            print(f"\n--- Structure of {t_name} ---")
            cursor.execute(f"PRAGMA table_info({t_name})")
            for col in cursor.fetchall():
                print(col)
            
            cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
            print(f"Rows: {cursor.fetchone()[0]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
