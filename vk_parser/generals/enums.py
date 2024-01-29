from enum import StrEnum


class ParserTypes(StrEnum):
    VK_SIMPLE_PARSED_POSTS = "VK_SIMPLE_PARSED_POSTS"


class RequestStatus(StrEnum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EMPTY = "EMPTY"
    SUCCESSFUL = "SUCCESSFUL"
