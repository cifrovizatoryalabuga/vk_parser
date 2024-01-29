from datetime import datetime

from pydantic import BaseModel


class VkGroupPost(BaseModel):
    created_at: datetime
    updated_at: datetime
    id: int
    vk_group_id: int
    posted_at: datetime
    text: str
