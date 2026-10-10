import os
import sys
import json
import psycopg

def check_supabase_db():
    db_url = os.environ.get(
        "DATABASE_URL", 
        "postgresql://postgres.aytvdrnkbjgaqqjuntoj:GQT%40studentportal@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    print("--- 1. Testing Direct Supabase DB Connection ---")
    try:
        with psycopg.connect(db_url, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), version();")
                res = cur.fetchone()
                print(f"Connected to Database: {res[0]}")
                print(f"PostgreSQL Version: {res[1]}")
                
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
                tables = [row[0] for row in cur.fetchall()]
                print(f"Public tables count in Supabase: {len(tables)}")
                print(f"Tables sample: {tables[:12]}")
                return True
    except Exception as e:
        print(f"Supabase DB Connection Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = check_supabase_db()
    sys.exit(0 if success else 1)
