from core.parsing import clamp

def calc_stress_index(rhr: int, energy: float) -> dict:
    """
    Stress Index (0–20) — MVP модель.
    Потом подгоним пороги 1-в-1 под таблицу.
    """

    # Пульс: ниже — лучше (ресурс выше)
    if rhr <= 58:
        pulse_score = 4
    elif rhr <= 68:
        pulse_score = 3
    elif rhr <= 78:
        pulse_score = 2
    else:
        pulse_score = 1

    # Энергия: выше — лучше (ресурс выше)
    if energy >= 9:
        energy_score = 6
    elif energy >= 8:
        energy_score = 5
    elif energy >= 7:
        energy_score = 4
    elif energy >= 6:
        energy_score = 3
    else:
        energy_score = 2

    # Приводим к диапазону ближе к 0–20
    idx = int(clamp(pulse_score + energy_score + 10, 0, 20))

    return {
        "stress_index": idx,
        "components": {"pulse": pulse_score, "energy": energy_score},
    }
