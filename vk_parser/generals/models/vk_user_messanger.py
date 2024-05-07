from pydantic import BaseModel, ConfigDict


class SendAccounts(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    login: str
    password: str
    secret_token: str
    proxy: str
    successful_messages: int
    error_status: str
    user_link: str
    expire_timestamp: str


class Messages(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    order: int
    message: str
