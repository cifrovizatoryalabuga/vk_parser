from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class DeleteMessagesBDHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def get(self) -> web.Response:
        print(1)
        await self.parser_request_storage.delete_messages()

        location = self.request.app.router["parser_request_messages_template"].url_for()
        raise web.HTTPFound(location=location)
