from pydantic import BaseModel, ConfigDict
from yarl import URL

from vk_parser.generals.enums import MessagesStatus


class VkMessageSend(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    group_url: URL
    group_name: str
    status: MessagesStatus
    vk_user_id: str
    message: str
