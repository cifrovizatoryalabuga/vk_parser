from collections.abc import Mapping
from typing import Any
import re

import aiohttp_jinja2
from aiohttp import web
from datetime import datetime

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class LoginUserTemplateHandler(web.View, DependenciesMixin, ListMixin):
    @aiohttp_jinja2.template("./authorization/login.html.j2")
    async def get(self) -> Mapping[str, Any]:
        params = self._parse()

        pagination = await self.auth_storage.paginate_users(
            page=params.page,
            page_size=params.page_size,
        )

        return {
            "pagination": pagination,
        }
