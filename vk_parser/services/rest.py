import logging
from collections.abc import Sequence
from itertools import chain
from typing import Any

import aiohttp_cors
from aio_pika.patterns import Master
from aiohttp import hdrs
from aiohttp.web import AbstractRoute, Application
from aiomisc.service.aiohttp import AIOHTTPService

from vk_parser.handlers.parser_request_create import ParserRequestCreateHandler
from vk_parser.handlers.parser_request_detail import ParserRequestDetailHandler
from vk_parser.handlers.parser_request_list import ParserRequestListHandler
from vk_parser.handlers.ping import PingHandler
from vk_parser.storages.parser_request import ParserRequestStorage
from vk_parser.storages.ping import PingStorage

log = logging.getLogger(__name__)

MEGABYTE = 1024**2
ALLOWED_METHODS = (hdrs.METH_OPTIONS, hdrs.METH_GET, hdrs.METH_POST)

HandlersType = tuple[tuple[str, str, Any], ...]


class REST(AIOHTTPService):
    __dependencies__ = (
        "parser_request_storage",
        "ping_storage",
        "amqp_master",
    )

    parser_request_storage: ParserRequestStorage
    ping_storage: PingStorage
    amqp_master: Master

    ROUTES: HandlersType = (
        (hdrs.METH_GET, "/api/v1/ping/", PingHandler),
        (hdrs.METH_POST, "/api/v1/parsers/", ParserRequestCreateHandler),
        (hdrs.METH_GET, "/api/v1/parsers/", ParserRequestListHandler),
        (hdrs.METH_GET, "/api/v1/parsers/{id}/", ParserRequestDetailHandler),
    )

    async def create_application(self) -> Application:
        app = Application(
            client_max_size=10 * MEGABYTE,
        )
        self._configure_routes(app)
        self._set_dependencies(app)
        return app

    def _configure_routes(self, app: Application) -> None:
        for method, path, handler in self.ROUTES:
            app.router.add_route(method, path, handler)

    def _set_dependencies(self, app: Application) -> None:
        for name in chain(self.__dependencies__, self.__required__):
            app[name] = getattr(self, name)

    def _configure_cors(
        self, app: Application, routes: Sequence[AbstractRoute]
    ) -> None:
        resource_options = aiohttp_cors.ResourceOptions(
            allow_headers="*",
            allow_methods=ALLOWED_METHODS,
            allow_credentials=True,
            max_age=3600,
        )
        defaults = {str(url): resource_options for url in self.access_allow_origins}
        cors = aiohttp_cors.setup(app=app, defaults=defaults)
        for route in routes:
            cors.add(route)
