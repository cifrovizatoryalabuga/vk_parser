from collections.abc import Mapping
from typing import Any
import jwt

import aiohttp_jinja2
from aiohttp import web
import datetime

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class LoginUserTemplateHandler(web.View, DependenciesMixin, ListMixin):
    @aiohttp_jinja2.template("./authorization/login.html.j2")
    async def get(self) -> Mapping[str, Any]:
        if self.request.cookies.get('jwt_token'):
            location = self.request.app.router["admin"].url_for()
            raise web.HTTPFound(location=location)

    @aiohttp_jinja2.template("./authorization/login.html.j2")
    async def post(self) -> web.Response:
        input_data = await self.request.post()

        login = input_data['login']
        password = input_data['password']

        authorization = await self.auth_storage.authorization_user(login=login, password=password)

        if authorization:

            user = await self.auth_storage.get_user_by_login(login)
            role = user.role
            user_id = user.id

            if role in ['admin', 'user']:
                token = jwt.encode({'login': login, 'role': role, "user_id": user_id, 'exp': datetime.datetime.now() + datetime.timedelta(hours=1)}, 'secret', algorithm='HS256')
            else:
                return {
                    "no_role": True,
                    }

            location = self.request.app.router["admin"].url_for()
            response =  web.HTTPFound(location=location)
            response.set_cookie('jwt_token', token)
            return response
        else:
            return {"no_user": True}
