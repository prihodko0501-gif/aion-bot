# Recovery model
# Скорость восстановления

def build_recovery_model(physiology: dict, nervous: dict):

    recovery_index = physiology.get("recovery_index", 0)
    nervous_balance = nervous.get("nervous_balance", 0)

    recovery_speed = recovery_index * 0.7 + nervous_balance * 0.3

    return {
        "recovery_speed": round(recovery_speed, 2)
    }
