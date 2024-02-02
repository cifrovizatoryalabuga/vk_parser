from datetime import datetime


def datetime_format(value: datetime, format: str = "%H:%M:%S %d.%m.%y") -> str:
    return value.strftime(format)
