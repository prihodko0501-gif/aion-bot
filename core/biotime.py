from core.human.human_architecture import build_human_architecture


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

    value = (
        sleep * 1.2
        + recovery * 1.2
        - stress
        - pressure_penalty
        - drop_penalty
        - risk_penalty
    )

    return clamp(round(value, 1), 0.0, 12.0)


def calculate_aion_state(payload: dict) -> dict:
    """
    Полный расчёт состояния организма AION
    """

    human = build_human_architecture(payload)

    sleep = payload.get("sleep", 0)
    stress = payload.get("stress", 0)

    recovery = human["recovery"]["recovery_speed"]

    biotime = calculate_biotime_pro(
        sleep=sleep,
        recovery=recovery,
        stress=stress
    )

    return {
        "biotime": biotime,
        "human_model": human
    }