from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vk_parser.generals.enums import SendMessageStatus


class SendMessages(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    parser_request_id: int
    task_name: str
    status: SendMessageStatus
    successful_messages: int
    necessary_messages: int
    created_at: datetime
    finished_at: datetime | None
    error_message: str | None
