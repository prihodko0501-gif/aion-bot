from datetime import date
from database.db import get_connection


def save_biotime(user_id, biotime, aion_index):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        insert into biotime_entries (user_id, date, biotime, aion_index)
        values (%s, %s, %s, %s)
        on conflict (user_id, date)
        do update set
        biotime = excluded.biotime,
        aion_index = excluded.aion_index;
        """,
        (user_id, date.today(), biotime, aion_index)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_history(user_id, days=7):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        select date, biotime, aion_index
        from biotime_entries
        where user_id = %s
        order by date desc
        limit %s
        """,
        (user_id, days)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows
