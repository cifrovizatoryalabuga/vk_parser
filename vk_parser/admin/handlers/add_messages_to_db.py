from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin, ListMixin
from vk_parser.utils.http import fast_json_response


class AddMessagesToBDHandler(web.View, DependenciesMixin, ListMixin):
    @timeout(5)
    async def get(self) -> web.Response:
        params = self._parse()

        pagination = await self.parser_request_storage.get_pagination_accounts(
            page=params.page,
            page_size=params.page_size,
        )
        return fast_json_response(data=pagination.model_dump(mode="json"))
