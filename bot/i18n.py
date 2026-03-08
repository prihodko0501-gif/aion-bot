LANGS = {
    "ru": {
        "start": "Старт",
        "new_calc": "Новый расчёт",
        "history": "История",
        "profile": "Профиль",
    },
    "en": {
        "start": "Start",
        "new_calc": "New calculation",
        "history": "History",
        "profile": "Profile",
    },
}


def t(lang: str, key: str) -> str:
    return LANGS.get(lang, LANGS["ru"]).get(key, key)