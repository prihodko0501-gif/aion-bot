# Nervous system model
# Нервная система

def build_nervous_system(payload: dict):

    latency = payload.get("latency_min", 0)
    awakenings = payload.get("awakenings", 0)
    morning = payload.get("morning_feel", 0)

    stress_load = latency * 0.1 + awakenings * 0.5
    nervous_balance = morning * 0.7 - stress_load * 0.3

    return {
        "stress_load": round(stress_load, 2),
        "nervous_balance": round(nervous_balance, 2)
    }
