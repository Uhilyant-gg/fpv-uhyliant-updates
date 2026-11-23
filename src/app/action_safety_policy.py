"""Pure classification of user-facing actions; no execution authority."""
NORMAL_NON_DESTRUCTIVE=frozenset({"find-camera","identify-camera","refresh-identity","verify-camera","connect-camera","show-video","connect-controller","calibrate-controller","diagnose","fix"})
DESTRUCTIVE_OR_SERVICE=frozenset({"update","fullflash","manual-firmware","sysupgrade","hardware-e2e"})

def classify_action(action):
    if action in NORMAL_NON_DESTRUCTIVE:return "normal"
    if action in DESTRUCTIVE_OR_SERVICE:return "guarded"
    return "unknown"

def can_auto_dispatch(action):
    return classify_action(action)=="normal"
