from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

ItemType = TypeVar("ItemType", bound=BaseModel)


class PaginationMeta(BaseModel):
    page: int
    pages: int
    total: int
    page_size: int


class PaginationResponse(BaseModel, Generic[ItemType]):
    meta: PaginationMeta
    items: list[ItemType]


class PaginationParams(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: PositiveInt = Field(default=1)
    page_size: PositiveInt = Field(default=20, le=100)
