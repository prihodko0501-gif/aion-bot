from .core import get_connection


def save_biotime_entry(
    user_id: int,
    payload: dict,
    biotime: float,
    status: str = "",
    level: str = "",
    advice: str = "",
    p_train: str = "",
    p_sleep: str = "",
    p_nutri: str = "",
):
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO biotime_entries (
            user_id,
            biotime
        )
        VALUES (%s, %s)
        """,
        (user_id, biotime)
    )

    conn.commit()
    cur.close()
    conn.close()


def save_entry(user_id: int, biotime: float):
    save_biotime_entry(user_id, {}, biotime)