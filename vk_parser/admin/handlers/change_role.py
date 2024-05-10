from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class ChangeRoleDBHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def post(self) -> web.Response:
        try:
            data = await self.request.json()
            user_id = data["userId"]
            role = data["role"]

            await self.auth_storage.change_role(user_id=int(user_id), role=role)

            return web.Response(
                text="<script>window.location.replace('/admin/all_users/');</script>",
                content_type="text/html",
                status=200,
            )

        except Exception as e:
            print(f"Error while processing request: {e}")
            return web.Response(status=500)
