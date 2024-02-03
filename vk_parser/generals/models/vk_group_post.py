from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VkGroupPost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
    id: int
    vk_post_id: int
    vk_group_id: int
    posted_at: datetime
    text: str
    user_vk_ids: Sequence[int]
    url: str
