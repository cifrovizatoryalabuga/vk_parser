from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin


class ParserRequestListMessagesTemplateHandler(
    web.View, DependenciesMixin, CreateMixin, ListMixin
):
    @aiohttp_jinja2.template("./parser_request/messages.html.j2")
    async def get(self) -> Mapping[str, Any]:
        params = self._parse()

        pagination = await self.parser_request_storage.admin_pagination_messages(
            page=params.page,
            page_size=10,
        )
        return {
            "pagination": pagination,
        }

    @aiohttp_jinja2.template("./parser_request/messages.html.j2")
    async def post(self) -> Mapping[str, Any]:
        input_data: str = await self.request.post()  # type: ignore
        await self.vk_storage.add_messages_bd(input_data["messages"].split("{}"))  # type: ignore

        if input_data is None:
            return {
                "error": True,
                "ParserTypes": "Input data empty",
            }

        location = self.request.app.router["parser_request_messages_template"].url_for()
        raise web.HTTPFound(location=location)
