from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, HttpUrl

from vk_parser.generals.enums import ParserTypes, RequestStatus


class VkInputData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parser_type: Literal[ParserTypes.VK_SIMPLE_PARSED_POSTS]
    group_url: HttpUrl
    posted_up_to: datetime
    max_age: int


class DetailParserRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    status: RequestStatus
    input_data: VkInputData
    result: dict[str, Any]
    finished_at: datetime | None
    error_message: str | None

    @property
    def parser_type(self) -> ParserTypes:
        return self.input_data.parser_type


class ParserRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    status: RequestStatus
    finished_at: datetime | None
    error_message: str | None
