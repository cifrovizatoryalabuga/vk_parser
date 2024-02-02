import logging
from http import HTTPStatus

from aiohttp.web import Response, View
from aiomisc import timeout

from vk_parser.admin.handlers.base import DependenciesMixin
from vk_parser.utils.http import fast_json_response

log = logging.getLogger(__name__)


class PingHandler(View, DependenciesMixin):
    @timeout(5)
    async def get(self) -> Response:
        db = await self.ping_storage.ping()
        deps = {
            "db": db,
        }
        if all(deps.values()):
            status_code = HTTPStatus.OK
        else:
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return fast_json_response(
            data=deps,
            status=status_code,
        )
