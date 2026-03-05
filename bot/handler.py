import time
import threading

from bot.api import (
    send_message, edit_message, try_delete_user_message,
    answer_callback, send_document_bytes
)
from bot.keyboards import (
    CB_MENU, CB_INFO, CB_SETTINGS, CB_PROFILE, CB_NEW, CB_NAV, CB_DYNAMICS, CB_HISTORY,
    CB_H7, CB_H14, CB_CSV, CB_ASSIST,
    main_menu_inline, back_inline, history_inline, after_calc_inline
)
from bot.texts import start_text, info_text, settings_text, pro_hint_text

from database.state import get_state, set_state, clear_flow
from database.entries import (
    save_biotime_entry, fetch_last_entry, fetch_history, fetch_history_limit, build_csv_bytes
)
from database.core import db_enabled

from core.parsing import parse_float, parse_int, parse_pressure
from core.pro import calc_biotime_pro

from core.assistant.prompts import intro_text as assist_intro_text
from core.assistant.rules import answer_rules as assist_answer_rules

from core.biotime.wizard import (
    STEP_BT_SLEEP_HOURS,
    STEP_BT_LATENCY_MIN,
    STEP_BT_AWAKENINGS,
    STEP_BT_MORNING_FEEL,
    STEP_BT_RHR,
    STEP_BT_ENERGY,
    STEP_BT_PRESSURE,
    prompt,
    next_step,
)

from core.biotime.model import (
    compute_biotime_from_payload,
    classify_biotime,
    result_block,
)

from core.profile import profile_text
from core.history import history_block