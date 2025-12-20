from datetime import datetime, timedelta


def is_night() -> bool:
    h = datetime.now().hour
    return h >= 23 or h < 7


def long_pause(last: datetime | None, minutes: int = 60) -> bool:
    if not last:
        return False
    return datetime.now() - last > timedelta(minutes=minutes)
