state_cache = {}


def get_state(user_id: int):
    return state_cache.get(user_id, {})


def set_state(user_id: int, **kwargs):
    current = state_cache.get(user_id, {})
    current.update(kwargs)
    state_cache[user_id] = current
    return current


def clear_state(user_id: int):
    state_cache[user_id] = {}