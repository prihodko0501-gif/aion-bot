# Adaptation capacity
# Адаптационная ёмкость организма

def build_adaptation(payload: dict):

    training_load = payload.get("training_load", 0)
    sleep = payload.get("sleep_hours", 0)
    recovery = payload.get("recovery_index", 0)

    adaptation_capacity = (
        sleep * 0.4 +
        recovery * 0.4 -
        training_load * 0.2
    )

    return {
        "adaptation_capacity": round(adaptation_capacity, 2)
    }
