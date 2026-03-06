from .core import get_connection


def save_entry(user_id: int, biotime: float):

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO biotime_entries (user_id, biotime)
        VALUES (%s, %s)
        """,
        (user_id, biotime)
    )

    conn.commit()

    cur.close()
    conn.close()