from datetime import datetime

_HISTORY = []


def add(user: str, bot: str):
    _HISTORY.append((datetime.now(), user, bot))


def recent(limit=5):
    return _HISTORY[-limit:]
