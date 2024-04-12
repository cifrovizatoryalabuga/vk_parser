from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class DeleteParserDBHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def post(self) -> web.Response:
        try:
            data = await self.request.json()
            parser_id = data["parserId"]

            await self.vk_storage.remove_parser_by_id(id=int(parser_id))

            return web.Response(
                text="<script>window.location.replace('/admin/parsers/');</script>",
                content_type="text/html",
                status=200,
            )

        except Exception as e:
            print(f"Error while processing request: {e}")
            return web.Response(status=500)
