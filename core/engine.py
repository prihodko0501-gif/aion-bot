from core.sleep import calculate_sleep_score
from core.stress import calculate_stress_score
from core.pressure import calculate_pressure_score
from core.recovery import calculate_recovery_score
from core.biotime import calculate_biotime


def run_aion_engine(data: dict) -> dict:
    sleep_score = calculate_sleep_score(
        data.get("sleep_hours", 0),
        data.get("sleep_quality", 0),
    )

    stress_score = calculate_stress_score(
        data.get("stress_level", 0),
    )

    pressure_score = calculate_pressure_score(
        data.get("systolic", 0),
        data.get("diastolic", 0),
    )

    recovery_score = calculate_recovery_score(
        sleep_score,
        stress_score,
        pressure_score,
    )

    biotime = calculate_biotime(
        sleep_score,
        stress_score,
        pressure_score,
        recovery_score,
    )

    return {
        "sleep_score": sleep_score,
        "stress_score": stress_score,
        "pressure_score": pressure_score,
        "recovery_score": recovery_score,
        "biotime": biotime,
    }
