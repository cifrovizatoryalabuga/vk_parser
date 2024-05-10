from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class LogoutUser(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def get(self) -> web.Response:
        response = web.HTTPFound("/admin/login/")  # Редирект на страницу входа
        response.del_cookie("jwt_token")
        return response
