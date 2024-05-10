from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import jwt
from aiohttp import web

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin
from vk_parser.generals.enums import UserRoles


class IndexTemplateHandler(web.View, DependenciesMixin, ListMixin):
    @aiohttp_jinja2.template("./authorization/admin_panel.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            if decoded_jwt["role"] != UserRoles.ADMIN:
                response = web.HTTPFound("/admin/parsers/")
                raise response

            params = self._parse()

            all_users = await self.auth_storage.get_all_users()
            all_users_data = {}
            for user in all_users:
                all_users_data[user.id] = user.login

            response_data = {"parser": self.request.query.get("parser")}

            if response_data["parser"] and response_data["parser"] != "all_parsers":
                user = await self.auth_storage.get_user_by_login(response_data["parser"])
                user_id = user.id
                pagination = await self.parser_request_storage.admin_pagination_filtered(
                    page=params.page,
                    page_size=params.page_size,
                    user_id=user_id,
                )
            else:
                pagination = await self.parser_request_storage.admin_pagination(
                    page=params.page,
                    page_size=params.page_size,
                )
            return {
                "all_users": all_users_data,
                "user_info": decoded_jwt,
                "pagination": pagination,
            }
        else:
            response = web.HTTPFound("/admin/login/")
            raise response
