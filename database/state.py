state_cache = {}

def get_state(user_id: int):
    return state_cache.get(user_id)

def set_state(user_id: int, state: dict):
    state_cache[user_id] = state