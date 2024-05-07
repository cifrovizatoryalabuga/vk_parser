from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vk_parser.generals.enums import VkDialogsStatus


class VkDialogs(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    send_account_id: int
    vk_group_user_id: int
    status: VkDialogsStatus
    created_at: datetime
    finished_at: datetime | None


class VkMessages(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dialog_id: int
    message_id: int
    created_at: datetime
