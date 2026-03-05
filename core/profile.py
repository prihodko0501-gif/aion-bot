def profile_text(profile: dict | None) -> str:
    if not profile:
        return (
            "🧠 Профиль (MVP)\n\n"
            "Пока нет данных профиля.\n"
            "Сделай несколько расчётов и заполни профиль позже."
        )

    lines = ["🧠 Профиль (MVP)\n"]
    for k, v in profile.items():
        lines.append(f"• {k}: {v}")
    return "\n".join(lines)
