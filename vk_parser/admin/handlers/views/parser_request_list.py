from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web
import jwt

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class ParserRequestListTemplateHandler(web.View, DependenciesMixin, ListMixin):
    @aiohttp_jinja2.template("./parser_request/list.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get('jwt_token')
        if jwt_token:

            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)
            try:
                user = await self.auth_storage.get_user_by_login(decoded_jwt['login'])
                user_id = user.id
            except AttributeError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            params = self._parse()

            pagination = await self.parser_request_storage.admin_pagination_by_user(
                page=params.page,
                page_size=params.page_size,
                user_id=user_id,
            )
            return {
                "user_info": decoded_jwt,
                "pagination": pagination,
            }
        else:
            response = web.HTTPFound('/admin/login/')
            raise response
