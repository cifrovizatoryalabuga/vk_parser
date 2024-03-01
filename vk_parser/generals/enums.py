from enum import StrEnum, unique


@unique
class ParserTypes(StrEnum):
    VK_DOWNLOAD_AND_PARSED_POSTS = "VK_DOWNLOAD_AND_PARSED_POSTS"
    VK_SIMPLE_DOWNLOAD = "VK_SIMPLE_DOWNLOAD"


VK_PARSER_TYPES = (
    ParserTypes.VK_SIMPLE_DOWNLOAD,
    ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS,
)


@unique
class RequestStatus(StrEnum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    EMPTY = "EMPTY"
    SUCCESSFUL = "SUCCESSFUL"

@unique
class MessagesStatus(StrEnum):
    SENDING = "SENDING"
    COMPLETE = "COMPLETE"
    STARTING = "STARTING"
    FAILED = "FAILED"
    EMPTY = "EMPTY"
    

@unique
class RequestMessage(StrEnum):
    EMPTY_USERS = "Empty users"
    EMPTY_POSTS = "Posts with users not found"
    EMPTY_INTERSECTION = "Empty intersection users and posts"
