from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin


class DeleteAccountsBDHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def post(self) -> web.Response:
        await self.parser_request_storage.delete_accounts()

        location = self.request.app.router["parser_request_accounts_template"].url_for()
        raise web.HTTPFound(location=location)
