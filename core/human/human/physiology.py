# AION Human Architecture
# Physiology module
# Физиология организма

def build_physiology(payload: dict):
    """
    Анализ физиологии человека
    """

    sleep_hours = payload.get("sleep_hours", 0)
    rhr = payload.get("rhr", 0)
    energy = payload.get("energy", 0)

    recovery_index = (
        sleep_hours * 0.4 +
        energy * 0.4 +
        max(0, (80 - rhr)) * 0.2
    )

    return {
        "sleep_hours": sleep_hours,
        "rhr": rhr,
        "energy": energy,
        "recovery_index": round(recovery_index, 2)
    }
