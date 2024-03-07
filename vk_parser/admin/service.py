import logging
from collections.abc import Sequence
from itertools import chain
from pathlib import Path
from typing import Any

import aiohttp_cors
import aiohttp_jinja2
import jinja2
from aio_pika.patterns import Master
from aiohttp import hdrs
from aiohttp.web import AbstractRoute, Application
from aiomisc.service.aiohttp import AIOHTTPService

from vk_parser.admin.handlers.add_messages_to_db import AddMessagesToBDHandler
from vk_parser.admin.handlers.add_users_to_db import AddUsersToBDHandler
from vk_parser.admin.handlers.delete_accounts_db import DeleteAccountsBDHandler
from vk_parser.admin.handlers.delete_messages_db import DeleteMessagesBDHandler
from vk_parser.admin.handlers.parser_request_create import ParserRequestCreateHandler
from vk_parser.admin.handlers.parser_request_detail import ParserRequestDetailHandler
from vk_parser.admin.handlers.parser_request_list import ParserRequestListHandler
from vk_parser.admin.handlers.ping import PingHandler
from vk_parser.admin.handlers.views.index import IndexTemplateHandler
from vk_parser.admin.handlers.views.parser_request_accounts import (
    ParserRequestListAccountsTemplateHandler,
)
from vk_parser.admin.handlers.views.parser_request_create import (
    ParserRequestCreateTemplateHandler,
)
from vk_parser.admin.handlers.views.parser_request_detail import (
    ParserRequestDetailTemplateHandler,
)
from vk_parser.admin.handlers.views.parser_request_list import (
    ParserRequestListTemplateHandler,
)
from vk_parser.admin.handlers.views.parser_request_messages import (
    ParserRequestListMessagesTemplateHandler,
)
from vk_parser.admin.handlers.views.redirect_to_admin import RedirectToAdminHandler
from vk_parser.admin.handlers.views.vk_group_user_download_csv import (
    VkGroupUserDownloadCsvHandler,
)
from vk_parser.storages.parser_request import ParserRequestStorage
from vk_parser.storages.ping import PingStorage
from vk_parser.storages.vk import VkStorage
from vk_parser.utils.filters import datetime_format

log = logging.getLogger(__name__)

MEGABYTE = 1024**2
ALLOWED_METHODS = (hdrs.METH_OPTIONS, hdrs.METH_GET, hdrs.METH_POST)

HandlersType = tuple[tuple[str, str, Any, str], ...]
PROJECT_PATH = Path(__file__).parent.parent.resolve()


class Admin(AIOHTTPService):
    __dependencies__ = (
        "parser_request_storage",
        "ping_storage",
        "vk_storage",
        "amqp_master",
    )

    parser_request_storage: ParserRequestStorage
    ping_storage: PingStorage
    vk_storage: VkStorage
    amqp_master: Master

    ROUTES: HandlersType = (
        (hdrs.METH_GET, "/api/v1/ping/", PingHandler, "ping"),
        (
            hdrs.METH_POST,
            "/api/v1/parsers/",
            ParserRequestCreateHandler,
            "parser_request_create",
        ),
        (
            hdrs.METH_GET,
            "/api/v1/parsers/",
            ParserRequestListHandler,
            "parser_request_list",
        ),
        (
            hdrs.METH_GET,
            "/api/v1/parsers/{id}/",
            ParserRequestDetailHandler,
            "parser_request_detail",
        ),
        (
            hdrs.METH_GET,
            "/api/v1/add_accounts_db/",
            AddUsersToBDHandler,
            "parser_request_add_accounts",
        ),
        (
            hdrs.METH_GET,
            "/api/v1/add_messages_db/",
            AddMessagesToBDHandler,
            "parser_request_add_messages",
        ),
        (
            hdrs.METH_GET,
            "/api/v1/delete_messages_db/",
            DeleteMessagesBDHandler,
            "parser_request_delete_messages",
        ),
        (
            hdrs.METH_GET,
            "/api/v1/delete_accounts_db/",
            DeleteAccountsBDHandler,
            "parser_request_delete_accounts",
        ),
        (hdrs.METH_GET, "/", RedirectToAdminHandler, "redirect_to_admin"),
        (hdrs.METH_GET, "/admin/", IndexTemplateHandler, "admin"),
        (
            hdrs.METH_GET,
            "/admin/parsers/",
            ParserRequestListTemplateHandler,
            "parser_request_list_template",
        ),
        (
            hdrs.METH_GET,
            "/admin/parsers/create/",
            ParserRequestCreateTemplateHandler,
            "parser_request_create_template",
        ),
        (
            hdrs.METH_POST,
            "/admin/parsers/create/",
            ParserRequestCreateTemplateHandler,
            "parser_request_create_template",
        ),
        (
            hdrs.METH_GET,
            "/admin/parsers/{id}/",
            ParserRequestDetailTemplateHandler,
            "parser_request_detail_template",
        ),
        (
            hdrs.METH_POST,
            "/admin/parsers/{id}/",
            ParserRequestDetailTemplateHandler,
            "parser_request_detail_template",
        ),
        (
            hdrs.METH_GET,
            "/admin/parsers/{id}/users/",
            VkGroupUserDownloadCsvHandler,
            "parser_request_users_download",
        ),
        (
            hdrs.METH_GET,
            "/admin/accounts/",
            ParserRequestListAccountsTemplateHandler,
            "parser_request_accounts_template",
        ),
        (
            hdrs.METH_POST,
            "/admin/accounts/",
            ParserRequestListAccountsTemplateHandler,
            "parser_request_accounts_template",
        ),
        (
            hdrs.METH_GET,
            "/admin/messages/",
            ParserRequestListMessagesTemplateHandler,
            "parser_request_messages_template",
        ),
        (
            hdrs.METH_POST,
            "/admin/messages/",
            ParserRequestListMessagesTemplateHandler,
            "parser_request_messages_template",
        ),
    )

    async def create_application(self) -> Application:
        app = Application(
            client_max_size=10 * MEGABYTE,
        )
        self._configure_routes(app)
        self._set_dependencies(app)
        self._set_templates(app)
        return app

    def _configure_routes(self, app: Application) -> None:
        for method, path, handler, name in self.ROUTES:
            app.router.add_route(method, path, handler, name=name)
        app.router.add_static(prefix="/static", path=PROJECT_PATH / "admin/static")

    def _set_dependencies(self, app: Application) -> None:
        for name in chain(self.__dependencies__, self.__required__):
            app[name] = getattr(self, name)

    def _set_templates(self, app: Application) -> None:
        aiohttp_jinja2.setup(
            app=app,
            loader=jinja2.FileSystemLoader(PROJECT_PATH / "admin/templates"),
            filters={"datetime_format": datetime_format},
        )

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
