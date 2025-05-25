from datetime import datetime


def is_valid_date(fecha):
    if isinstance(fecha, datetime):
        return True
    try:
        datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S%z")
        return True
    except Exception:
        return False
