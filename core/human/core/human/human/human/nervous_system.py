# AION Human Architecture
# Центральная модель человека

from .physiology import build_physiology
from .nervous_system import build_nervous_system
from .adaptation import build_adaptation
from .recovery_model import build_recovery


def build_human_architecture(payload: dict):
    """
    Сборка полной архитектуры человека AION
    """

    physiology = build_physiology(payload)
    nervous = build_nervous_system(payload)
    adaptation = build_adaptation(payload)
    recovery = build_recovery(payload)

    human_model = {
        "physiology": physiology,
        "nervous_system": nervous,
        "adaptation": adaptation,
        "recovery": recovery
    }

    return human_model
