# Adaptation capacity
# Адаптационная ёмкость

def build_adaptation(physiology: dict, nervous: dict):

    recovery_index = physiology.get("recovery_index", 0)
    nervous_balance = nervous.get("nervous_balance", 0)

    adaptation_capacity = (
        recovery_index * 0.6 +
        nervous_balance * 0.4
    )

    load_tolerance = adaptation_capacity * 10

    return {
        "adaptation_capacity": round(adaptation_capacity, 2),
        "load_tolerance": round(load_tolerance, 2)
    }
