from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from vk_parser.admin.handlers.base import DependenciesMixin
from vk_parser.generals.enums import ParserTypes


class ParserRequestDetailTemplateHandler(web.View, DependenciesMixin):
    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def get(self) -> Mapping[str, Any]:
        parser_request_id = self._get_id()
        parser_request = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )
        if parser_request is None:
            raise HTTPNotFound
        users = None
        if parser_request.parser_type == ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS:
            users = await self.vk_storage.get_users_by_parser_request_id(
                parser_request_id
            )
        return {
            "parser_request": parser_request,
            "users": users,
        }

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")
