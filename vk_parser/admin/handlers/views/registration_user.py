from collections.abc import Mapping
from typing import Any
import re

import aiohttp_jinja2
from aiohttp import web
from datetime import datetime

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin, CreateMixin
from vk_parser.generals.models.auth import AuthUser as AuthUserForm


class RegistrationUserTemplateHandler(web.View, DependenciesMixin, ListMixin, CreateMixin):
    @aiohttp_jinja2.template("./authorization/registration.html.j2")
    async def get(self) -> Mapping[str, Any]:
        return {}

    @aiohttp_jinja2.template("./authorization/registration.html.j2")
    async def post(self) -> Mapping[str, Any]:
        login_pattern = r'^[A-Z][a-z]*_[A-Z][a-z]*$'
        password_pattern = r'^[a-zA-Z0-9!@#$%^&*()_+{}|:"<>?]{6,}$'
        input_data = await self.request.post()
        if not re.match(login_pattern, input_data['login']) or not re.match(password_pattern, input_data['password']):
            return {
                "error": True
            }

        login = input_data['login']
        password = input_data['password']

        if await self.auth_storage.create(
            {
                "login": login,
                "password": password,
                "allowed": False,
                "created_at": datetime.now(),
                "role": "user",
            }
        ) == "Duplicate":
            return {
                "dublicate": True
            }

        location = self.request.app.router["admin"].url_for()
        raise web.HTTPFound(location=location)
