from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class ParserRequestListMessagesTemplateHandler(web.View, DependenciesMixin, ListMixin):
    @aiohttp_jinja2.template("./parser_request/send_messages.html.j2")
    async def get(self) -> Mapping[str, Any]:
        params = self._parse()

        pagination = await self.parser_request_storage.admin_pagination(
            page=params.page,
            page_size=params.page_size,
        )
        return {
            "pagination": pagination,
        }