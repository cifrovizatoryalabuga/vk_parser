from pydantic import BaseModel
from yarl import URL

from vk_parser.generals.enums import RequestStatus


class VkGroupRequest(BaseModel):
    id: int
    url: URL
    status: RequestStatus
        