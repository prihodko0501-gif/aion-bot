BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "❤️ Pressure"
BTN_INFO = "ℹ️ Info"


def main_menu_reply():
    return {
        "keyboard": [
            [{"text": BTN_BIOTIME}],
            [{"text": BTN_SLEEP}, {"text": BTN_CNS}],
            [{"text": BTN_RECOVERY}, {"text": BTN_PRESSURE}],
            [{"text": BTN_INFO}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "is_persistent": True,
    }