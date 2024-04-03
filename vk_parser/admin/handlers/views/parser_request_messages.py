from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import jwt
from aiohttp import web

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin


class ParserRequestListMessagesTemplateHandler(
    web.View, DependenciesMixin, CreateMixin, ListMixin
):
    @aiohttp_jinja2.template("./parser_request/messages.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            user = await self.auth_storage.get_user_by_login(decoded_jwt["login"])
            user_id = user.id
            params = self._parse()

            pagination = await self.parser_request_storage.admin_pagination_messages(
                page=params.page,
                page_size=10,
                user_id=user_id,
            )
            return {
                "user_info": decoded_jwt,
                "pagination": pagination,
            }
        else:
            response = web.HTTPFound("/admin/login/")
            raise response

    @aiohttp_jinja2.template("./parser_request/messages.html.j2")
    async def post(self) -> Mapping[str, Any]:
        input_data: str = await self.request.post()
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            user = await self.auth_storage.get_user_by_login(decoded_jwt["login"])
            user_id = user.id

        await self.vk_storage.add_messages_bd(
            input_data["messages"].split("{}"), user_id=user_id
        )

        if input_data is None:
            return {
                "error": True,
                "ParserTypes": "Input data empty",
            }

        location = self.request.app.router["parser_request_messages_template"].url_for()
        raise web.HTTPFound(location=location)
