from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin
from vk_parser.generals.enums import ParserTypes, RequestStatus
from vk_parser.generals.models.parser_request import (
    ParsePostsVkInputData,
    SimpleVkInputData,
)


class ParserRequestCreateTemplateHandler(web.View, DependenciesMixin, CreateMixin):
    @aiohttp_jinja2.template("./parser_request/create.html.j2")
    async def get(self) -> Mapping[str, Any]:
        return {
            "ParserTypes": ParserTypes,
        }

    @aiohttp_jinja2.template("./parser_request/create.html.j2")
    async def post(self) -> Mapping[str, Any]:
        input_data = await self.parse_form(
            schemas=[ParsePostsVkInputData, SimpleVkInputData]
        )
        if input_data is None:
            return {
                "error": True,
                "ParserTypes": ParserTypes,
            }
        parser_request = await self.parser_request_storage.create(
            input_data=input_data.model_dump(mode="json"),
        )
        if parser_request is None:
            raise HTTPInternalServerError(reason="Can't create parser request")
        await self.amqp_master.create_task(
            input_data.parser_type,  # type: ignore[attr-defined]
            kwargs=dict(
                parser_request_id=parser_request.id,
                input_data=input_data.model_dump(),
            ),
        )
        parser_request = (
            await self.parser_request_storage.update_status(
                id_=parser_request.id,
                status=RequestStatus.QUEUED,
            )
            or parser_request
        )
        location = self.request.app.router["parser_request_detail_template"].url_for(
            id=str(parser_request.id)
        )
        raise web.HTTPFound(location=location)
