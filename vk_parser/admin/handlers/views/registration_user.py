import os
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin
from vk_parser.generals.enums import UserRoles


class RegistrationUserTemplateHandler(web.View, DependenciesMixin, ListMixin, CreateMixin):
    @aiohttp_jinja2.template("./authorization/registration.html.j2")
    async def get(self) -> Mapping[str, Any]:
        if self.request.cookies.get("jwt_token"):
            location = self.request.app.router["admin"].url_for()
            raise web.HTTPFound(location=location)
        else:
            return {}

    @aiohttp_jinja2.template("./authorization/registration.html.j2")
    async def post(self) -> Mapping[str, Any]:
        login_pattern = r"^[A-Z][a-z]*_[A-Z][a-z]*$"
        password_pattern = r'^[a-zA-Z0-9!@#$%^&*()_+{}|:"<>?]{6,}$'
        input_data = await self.request.post()
        if not re.match(login_pattern, input_data["login"]) or not re.match(password_pattern, input_data["password"]):
            return {"error": True}

        login = input_data["login"]
        password = input_data["password"]

        if login == os.environ.get("ADMIN_USERNAME"):
            role = UserRoles.ADMIN
        else:
            role = UserRoles.UNAUTHORIZED

        if (
            await self.auth_storage.create(
                {
                    "login": login,
                    "password": password,
                    "allowed": False,
                    "created_at": datetime.now(),
                    "role": role,
                }
            )
            == "Duplicate"
        ):
            return {"dublicate": True}

        location = self.request.app.router["admin"].url_for()
        raise web.HTTPFound(location=location)
