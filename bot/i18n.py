DEFAULT_LANG = "ru"

RU = {
    "start_text": (
        "AION — система управления скоростью\n"
        "биологического износа на основании\n"
        "анализа твоей физиологии.\n\n"
        "Выбери действие:"
    ),
}

EN = {
    "start_text": (
        "AION — system to manage biological wear\n"
        "based on your physiology.\n\n"
        "Choose an action:"
    ),
}


def t(lang: str, key: str) -> str:
    lang = (lang or DEFAULT_LANG).lower()
    if lang.startswith("en"):
        return EN.get(key, RU.get(key, key))
    return RU.get(key, key)
