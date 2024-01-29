from pydantic import BaseModel, ConfigDict, HttpUrl


class VkGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parser_request_id: int
    vk_id: int
    url: HttpUrl
