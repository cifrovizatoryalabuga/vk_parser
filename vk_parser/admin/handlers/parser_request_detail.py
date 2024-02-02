from aiohttp.web import Response, View
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin
from vk_parser.utils.http import fast_json_response


class ParserRequestDetailHandler(View, DependenciesMixin):
    @timeout(5)
    async def get(self) -> Response:
        parser_request_id = self._get_id()
        obj = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )
        if obj is None:
            raise HTTPNotFound
        return fast_json_response(obj.model_dump(mode="json"))

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")
