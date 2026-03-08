import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())
        conn.commit()
    finally:
        cur.close()
        conn.close()