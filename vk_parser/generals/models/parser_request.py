from collections.abc import Sequence
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from vk_parser.generals.enums import ParserTypes, RequestStatus


class SimpleVkForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parser_type: Literal[ParserTypes.VK_SIMPLE_DOWNLOAD]
    group_url: HttpUrl
    max_age: int


class ParsePostsVkForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parser_type: Literal[ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS]
    group_url: HttpUrl
    posted_up_to: datetime
    max_age: int

    @field_validator("posted_up_to", mode="before")
    @classmethod
    def validate_posted_up_to(cls, v: Any) -> Any:
        try:
            return datetime.strptime(str(v), "%d.%m.%Y")
        except ValueError:
            return v


class UserStat(BaseModel):
    vk_id: int
    count: int


class Result(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    user_stat: Sequence[UserStat]


class DetailParserRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    status: RequestStatus
    input_data: ParsePostsVkForm | SimpleVkForm = Field(
        ...,
        discriminator="parser_type",
    )
    result_data: Result | None
    finished_at: datetime | None
    error_message: str | None

    @property
    def parser_type(self) -> ParserTypes:
        return self.input_data.parser_type


class ParserRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    status: RequestStatus
    finished_at: datetime | None
    error_message: str | None
