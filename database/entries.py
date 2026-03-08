from .core import get_connection


def ensure_table():
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS biotime_entries (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,

            sleep FLOAT,
            stress FLOAT,
            recovery FLOAT,

            pressure_sys INT,
            pressure_dia INT,
            pulse INT,

            biotime FLOAT,
            status TEXT,
            level TEXT,
            advice TEXT,

            protocol_training TEXT,
            protocol_sleep TEXT,
            protocol_nutrition TEXT,

            payload_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()