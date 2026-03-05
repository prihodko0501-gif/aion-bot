"""
Логика рефералки (MVP):
- у пользователя есть ref_code
- при старте по ссылке/коду сохраняем referred_by
- пишем событие referral_events
"""

def parse_ref_from_start(text: str) -> str | None:
    # Telegram: /start ABC12345
    parts = (text or "").strip().split()
    if len(parts) >= 2:
        return parts[1].strip()
    return None
