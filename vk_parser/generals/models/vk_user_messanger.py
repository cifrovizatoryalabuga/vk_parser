from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vk_parser.generals.enums import MessagesStatus


class SendAccounts(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    password: str
    secret_token: str
    successful_messages: int
    error_status: str
    user_link: str
    expire_timestamp: str


class Messages(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str


class SendMessangesDetail(BaseModel):
    """
    Модель для валидации базы данных SendMessanger.

    Args:
        BaseModel (_type_): Наследование с базовой модели.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status_message: MessagesStatus
    success_message: int
    created_at: datetime
    finished_at: datetime | None
