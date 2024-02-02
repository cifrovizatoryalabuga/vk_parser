from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from vk_parser.admin.handlers.base import DependenciesMixin


class IndexTemplateHandler(web.View, DependenciesMixin):
    @aiohttp_jinja2.template("./index.html.j2")
    async def get(self) -> Mapping[str, Any]:
        stat = await self.parser_request_storage.stat()
        return {
            "stat": stat,
        }
