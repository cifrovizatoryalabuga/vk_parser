from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from vk_parser.admin.handlers.base import DependenciesMixin


class ParserRequestDetailTemplateHandler(web.View, DependenciesMixin):
    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def get(self) -> Mapping[str, Any]:
        parser_request_id = self._get_id()
        obj = await self.parser_request_storage.get_detail_parser_request_by_id(
            id_=parser_request_id,
        )
        if obj is None:
            raise HTTPNotFound

        return {
            "parser_request": obj,
        }

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")
