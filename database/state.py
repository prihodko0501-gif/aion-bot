USER_STATE = {}


def get_state(chat_id):
    return USER_STATE.get(chat_id, {})


def set_state(chat_id, **kwargs):
    current = USER_STATE.get(chat_id, {})
    current.update(kwargs)
    USER_STATE[chat_id] = current
    return current


def clear_state(chat_id):
    USER_STATE.pop(chat_id, None)