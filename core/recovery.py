from core.parsing import clamp

def calc_biotime(sleep_index: float, stress_index: float, pressure_penalty: float,
                 drop_penalty: float = 0.0, risk_penalty: float = 0.0) -> dict:
    """
    Интегратор Recovery:
    Sleep(0–20) + Stress(0–20) + penalties -> BioTime(0–12) + режим.
    """

    # нормируем 0–20 -> 0–10
    sleep10 = (sleep_index / 20.0) * 10.0
    stress10 = (stress_index / 20.0) * 10.0

    bt = round(6.0 + sleep10 * 0.7 + (10.0 - stress10) * 0.5
               - pressure_penalty - drop_penalty - risk_penalty, 1)
    bt = clamp(bt, 0.0, 12.0)

    if bt < 7:
        regime = "ВОССТАНОВЛЕНИЕ"
    elif bt < 11.5:
        regime = "КОНТРОЛИРУЕМАЯ НАГРУЗКА"
    else:
        regime = "РОСТ"

    return {"biotime": bt, "regime": regime}
