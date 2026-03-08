def calculate_reward(referrals: int) -> dict:
    """
    Расчёт награды за рефералов
    """

    reward = referrals * 5

    return {
        "referrals": referrals,
        "reward_points": reward
    }
