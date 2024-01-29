from enum import StrEnum, unique


@unique
class MessageHdrs(StrEnum):
    EVENT_TYPE = "Event-Type"
    FROM = "From"
    RETRY_COUNT = "X-Retry-Count"
