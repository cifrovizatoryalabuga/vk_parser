from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import jwt
from aiohttp import web

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin


class AllUsersTemplateHandler(web.View, DependenciesMixin, CreateMixin, ListMixin):
    @aiohttp_jinja2.template("./authorization/all_users.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            if decoded_jwt["role"] != "admin":
                response = web.HTTPFound("/admin/parsers/")
                raise response

            response_data = {"role": self.request.query.get("user_role")}

            all_roles = []

            all_users = await self.auth_storage.get_all_users()
            all_users_data = {}
            for user in all_users:
                all_users_data[user.id] = user.login
                if user.role not in all_roles:
                    all_roles.append(user.role)

            params = self._parse()

            if response_data["role"]:
                pagination = await self.auth_storage.paginate_filtered_users(
                    page=params.page,
                    page_size=params.page_size,
                    role=response_data["role"],
                )
            else:
                pagination = await self.auth_storage.paginate_users(
                    page=params.page,
                    page_size=params.page_size,
                )

            return {
                "all_users": all_users_data,
                "all_roles": all_roles,
                "user_info": decoded_jwt,
                "pagination": pagination,
            }

        else:
            location = self.request.app.router["logout_user"].url_for()
            raise web.HTTPFound(location=location)
