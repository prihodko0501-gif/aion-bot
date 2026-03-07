import os
import psycopg2


def get_connection():
    url = os.getenv("DATABASE_URL")

    if not url:
        return None

    try:
        conn = psycopg2.connect(url, sslmode="require")
        conn.autocommit = True
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None