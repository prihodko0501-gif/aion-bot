from core.parsing import clamp

def calc_sleep_index(sleep_hours: float, latency_min: int, awakenings: int, morning_feel: float) -> dict:
    """
    Sleep Index (0–20) — MVP модель.
    Потом подгоним пороги 1-в-1 под твою таблицу.
    """

    # 1) Длительность (0–5)
    if sleep_hours >= 8:
        duration = 5
    elif sleep_hours >= 7:
        duration = 4
    elif sleep_hours >= 6:
        duration = 3
    elif sleep_hours >= 5:
        duration = 2
    else:
        duration = 1

    # 2) Засыпание (0–5)
    if latency_min <= 15:
        latency = 5
    elif latency_min <= 25:
        latency = 4
    elif latency_min <= 40:
        latency = 3
    elif latency_min <= 60:
        latency = 2
    else:
        latency = 1

    # 3) Пробуждения (0–5)
    if awakenings <= 1:
        frag = 5
    elif awakenings == 2:
        frag = 3
    elif awakenings == 3:
        frag = 2
    else:
        frag = 1

    # 4) Самочувствие утром (0–5)
    if morning_feel >= 9:
        morning = 5
    elif morning_feel >= 7:
        morning = 4
    elif morning_feel >= 5:
        morning = 3
    elif morning_feel >= 3:
        morning = 2
    else:
        morning = 1

    idx = int(clamp(duration + latency + frag + morning, 0, 20))
    return {
        "sleep_index": idx,
        "components": {
            "duration": duration,
            "latency": latency,
            "fragmentation": frag,
            "morning": morning,
        },
    }
