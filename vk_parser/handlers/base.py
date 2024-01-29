from typing import TypeVar

import orjson
from aiohttp.web import Request
from aiohttp.web_exceptions import HTTPBadRequest
from pydantic import BaseModel, ValidationError

from vk_parser.generals.models.pagination import PaginationParams
from vk_parser.storages.parser_request import ParserRequestStorage
from vk_parser.storages.ping import PingStorage
from vk_parser.utils.amqp.master import MsgPackMaster

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseHttpMixin:
    @property
    def request(self) -> Request:
        raise NotImplementedError


class DependenciesMixin(BaseHttpMixin):
    @property
    def parser_request_storage(self) -> ParserRequestStorage:
        return self.request.app["parser_request_storage"]

    @property
    def ping_storage(self) -> PingStorage:
        return self.request.app["ping_storage"]

    @property
    def amqp_master(self) -> MsgPackMaster:
        return self.request.app["amqp_master"]


class ListMixin(BaseHttpMixin):
    def _parse(self) -> PaginationParams:
        try:
            return PaginationParams.model_validate(self.request.query)
        except ValidationError:
            raise HTTPBadRequest(reason="Invalid pagination params")


class CreateMixin(BaseHttpMixin):
    async def _parse_json(self, schema_type: type[ModelType]) -> ModelType:
        try:
            data = await self.request.json(loads=orjson.loads)
            return schema_type.model_validate(data)
        except orjson.JSONDecodeError:
            raise HTTPBadRequest(reason="Invalid input params")
        except ValidationError as e:
            raise HTTPBadRequest(text=e.json())
