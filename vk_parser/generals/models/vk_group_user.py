from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict


class VkGroupUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vk_group_id: int
    vk_user_id: int
    raw_data: dict[str, Any]
    birth_date: date | None
    first_name: str | None
    last_name: str | None
    sex: str | None
    city: str | None
    last_visit_vk_date: date | None
