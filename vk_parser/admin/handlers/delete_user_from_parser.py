from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class DeleteUserFromParserBDHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def post(self) -> web.Response:
        try:
            data = await self.request.json()
            parser_id = data["parserId"]
            user_id = data["userId"]

            await self.vk_storage.remove_users_by_id(id=int(user_id))

            # Return a response that triggers a page refresh
            return web.Response(
                text="<script>window.location.replace('/admin/parsers/{parser_id}/');</script>",
                content_type="text/html",
                status=200,
            )

        except Exception as e:
            # Обработка ошибок
            print(f"Error while processing request: {e}")
            return web.Response(status=500)
