from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from vk_parser.generals.enums import MessagesStatus, SendMessagesTypes


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


class SendMessangerDetail(BaseModel):
    """
    Модель для валидации базы данных SendMessanger.

    Args:
        BaseModel (_type_): Наследование с базовой модели.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: Literal[SendMessagesTypes.MASS_MESSAGES_SENDER]
    status: MessagesStatus
    success_message: int
    total_message: int
    created_at: datetime
    finished_at: datetime | None
