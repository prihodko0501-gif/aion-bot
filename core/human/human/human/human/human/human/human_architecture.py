# AION Human Architecture Engine

from .physiology import build_physiology
from .nervous_system import build_nervous_system
from .adaptation import build_adaptation
from .recovery_model import build_recovery_model


def build_human_architecture(payload: dict, biotime: float):

    physiology = build_physiology(payload)

    nervous = build_nervous_system(payload)

    adaptation = build_adaptation(physiology, nervous)

    recovery = build_recovery_model(physiology, nervous)

    return {
        "physiology": physiology,
        "nervous_system": nervous,
        "adaptation": adaptation,
        "recovery": recovery,
        "biotime": biotime
    }
