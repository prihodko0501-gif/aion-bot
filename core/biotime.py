def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def calculate_biotime_pro(
    sleep: float,
    recovery: float,
    stress: float,
    pressure_penalty: float = 0.0,
    drop_penalty: float = 0.0,
    risk_penalty: float = 0.0,
) -> float:
    """
    AION PRO:
    BioTime = round((Sleep*1.2 + Recovery*1.2 - Stress) - PressurePenalty - DropPenalty - RiskPenalty, 1)
    затем clamp 0–12
    """
    value = (sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty
    return clamp(round(value, 1), 0.0, 12.0)
