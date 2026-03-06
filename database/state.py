state_cache = {}


def get_state(user_id: int):
    return state_cache.get(user_id, {})


def set_state(user_id: int, ui_message_id=None, step=None, mode=None, payload=None, state=None):
    if state is not None:
        state_cache[user_id] = state
        return

    current = state_cache.get(user_id, {})

    if ui_message_id is not None:
        current["ui_message_id"] = ui_message_id
    else:
        current.setdefault("ui_message_id", None)

    current["step"] = step
    current["mode"] = mode
    current["payload"] = payload if payload is not None else {}

    state_cache[user_id] = current


def clear_flow(user_id: int, keep_ui: bool = False):
    current = state_cache.get(user_id, {})

    ui_message_id = current.get("ui_message_id") if keep_ui else None

    state_cache[user_id] = {
        "ui_message_id": ui_message_id,
        "step": None,
        "mode": None,
        "payload": {},
    }