import os
import psycopg2


def get_connection():
    url = os.getenv("DATABASE_URL")

    if not url:
        return None

    return psycopg2.connect(url)