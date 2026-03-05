import psycopg2.extras
from database.core import db_enabled, db_exec

# memory fallback
MEM_STATE = {}

def get_state(chat_id: int):
    if db_enabled():
        row = db_exec("SELECT * FROM aion_state WHERE telegram_id=%s", (chat_id,), fetchone=True)
        if row:
            return {
                "telegram_id": chat_id,
                "ui_message_id": row.get("ui_message_id"),
                "step": row.get("step"),
                "mode": row.get("mode"),
                "payload": row.get("payload_json") or {},
            }

    st = MEM_STATE.get(chat_id) or {}
    return {
        "telegram_id": chat_id,
        "ui_message_id": st.get("ui_message_id"),
        "step": st.get("step"),
        "mode": st.get("mode"),
        "payload": st.get("payload") or {},
    }

def set_state(chat_id: int, ui_message_id=None, step=None, mode=None, payload=None):
    payload = payload or {}
     if chat_id not in MEM_STATE:
        MEM_STATE[chat_id] = {"ui_message_id": None, "step": None, "mode": None, "payload": {}}

    if ui_message_id is not None:
        MEM_STATE[chat_id]["ui_message_id"] = ui_message_id
    if step is not None:
        MEM_STATE[chat_id]["step"] = step
    if mode is not None:
        MEM_STATE[chat_id]["mode"] = mode
    if payload is not None:
        MEM_STATE[chat_id]["payload"] = payload

    if not db_enabled():
        return

    db_exec(
        """
        INSERT INTO aion_state (telegram_id, ui_message_id, step, mode, payload_json, updated_at)
        VALUES (%s,%s,%s,%s,%s,NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
            step=COALESCE(EXCLUDED.step, aion_state.step),
            mode=COALESCE(EXCLUDED.mode, aion_state.mode),
            payload_json=COALESCE(EXCLUDED.payload_json, aion_state.payload_json),
            updated_at=NOW();
        """,
        (
            chat_id,
            ui_message_id,
            step,
            mode,
            psycopg2.extras.Json(payload) if payload is not None else None,
        ),
    )

def clear_flow(chat_id: int, keep_ui=True):
    st = get_state(chat_id)
    ui_mid = st.get("ui_message_id") if keep_ui else None

    MEM_STATE[chat_id] = {"ui_message_id": ui_mid, "step": None, "mode": None, "payload": {}}

    if not db_enabled():
        return

    if keep_ui:
        db_exec(
            """
            INSERT INTO aion_state (telegram_id, ui_message_id, step, mode, payload_json, updated_at)
            VALUES (%s,%s,NULL,NULL,'{}'::jsonb,NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
                step=NULL,
                mode=NULL,
                payload_json='{}'::jsonb,
                updated_at=NOW();
            """,
            (chat_id, ui_mid),
        )
    else:
        db_exec("DELETE FROM aion_state WHERE telegram_id=%s", (chat_id,))
