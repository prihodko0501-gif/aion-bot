def track_referral(referrer_id: int, new_user_id: int) -> dict:
    """
    Отслеживание реферала
    """

    return {
        "referrer": referrer_id,
        "new_user": new_user_id,
        "status": "tracked"
    }
