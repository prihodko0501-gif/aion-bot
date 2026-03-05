from datetime import date
from database.db import get_connection


def ensure_schema():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        create table if not exists biotime_entries (
            id bigserial primary key,
            user_id bigint not null,
            date date not null,
            biotime numeric,
            aion_index integer,
            created_at timestamptz default now(),
            unique (user_id, date)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def save_biotime(user_id, biotime, aion_index=0):
    ensure_schema()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        insert into biotime_entries (user_id, date, biotime, aion_index)
        values (%s, %s, %s, %s)
        on conflict (user_id, date)
        do update set
            biotime = excluded.biotime,
            aion_index = excluded.aion_index;
    """, (user_id, date.today(), biotime, aion_index))

    conn.commit()
    cur.close()
    conn.close()