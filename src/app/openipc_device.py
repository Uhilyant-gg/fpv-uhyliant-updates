"""Verified OpenIPC identity normalization. Discovery hints alone never imply OpenIPC."""


def _text(value):
    return str(value).strip() if value is not None else ""


def normalize_openipc_identity(payload=None, evidence=None):
    data = dict(payload or {})
    evidence = list(evidence or [])
    verified = bool(data.get("verified")) or any("Majestic" in item or "vendor=OpenIPC" in item for item in evidence)
    if not verified:
        return {
            "verified": False,
            "platform": "",
            "soc": "",
            "sensor": "",
            "firmware": "",
            "majestic": "",
            "evidence": evidence,
        }
    return {
        "verified": True,
        "platform": _text(data.get("platform")),
        "soc": _text(data.get("soc")),
        "sensor": _text(data.get("sensor")),
        "firmware": _text(data.get("firmware")),
        "majestic": _text(data.get("majestic")),
        "evidence": evidence,
    }
