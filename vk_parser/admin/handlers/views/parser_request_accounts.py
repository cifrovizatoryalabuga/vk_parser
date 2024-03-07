from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin


class ParserRequestListAccountsTemplateHandler(
    web.View, DependenciesMixin, CreateMixin, ListMixin
):
    @aiohttp_jinja2.template("./parser_request/accounts.html.j2")
    async def get(self) -> Mapping[str, Any]:
        params = self._parse()

        pagination = await self.parser_request_storage.admin_pagination_accounts(
            page=params.page,
            page_size=params.page_size,
        )
        return {
            "pagination": pagination,
        }

    @aiohttp_jinja2.template("./parser_request/accounts.html.j2")
    async def post(self) -> Mapping[str, Any]:
        input_data = await self.request.post()
        await self.vk_storage.add_accounts_bd(input_data["accounts"].split(" "))  # type: ignore

        if input_data is None:
            return {
                "error": True,
                "ParserTypes": "Input data empty",
            }

        location = self.request.app.router["parser_request_accounts_template"].url_for()
        raise web.HTTPFound(location=location)
