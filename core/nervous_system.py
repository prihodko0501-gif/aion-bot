def calculate_nervous_system_state(stress: float, sleep: float) -> float:
    """
    Оценка состояния нервной системы
    """

    score = sleep - (stress * 0.8)

    if score < 0:
        score = 0

    return score
