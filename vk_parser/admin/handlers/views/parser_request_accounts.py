import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import jwt
from aiohttp import web

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin
from vk_parser.db.models.vk_user_messanger import SendAccounts
from vk_parser.utils.parsers import get_conversations_for_account

log = logging.getLogger(__name__)


class ParserRequestListAccountsTemplateHandler(
    web.View,
    DependenciesMixin,
    CreateMixin,
    ListMixin,
):
    async def _get_conversations_for_accounts(self, accounts: SendAccounts) -> int:
        tasks = [asyncio.create_task(get_conversations_for_account(account)) for account in accounts]
        conversations = await asyncio.gather(*tasks, return_exceptions=True)

        return [count if not isinstance(count, Exception) else 0 for count in conversations]

    @aiohttp_jinja2.template("./parser_request/accounts.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            user = await self.auth_storage.get_user_by_login(decoded_jwt["login"])
            user_id = user.id
            params = self._parse()

            pagination = await self.parser_request_storage.admin_pagination_accounts(
                page=params.page,
                page_size=params.page_size,
                user_id=user_id,
            )
            conversations = await self._get_conversations_for_accounts(pagination.items)
            pagination.items = list(zip(pagination.items, conversations))

            return {
                "user_info": decoded_jwt,
                "pagination": pagination,
            }
        else:
            response = web.HTTPFound("/admin/login/")
            raise response

    @aiohttp_jinja2.template("./parser_request/accounts.html.j2")
    async def post(self) -> Mapping[str, Any]:
        input_data = await self.request.post()
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)
            user = await self.auth_storage.get_user_by_login(decoded_jwt["login"])
            user_id = user.id

        await self.vk_storage.add_accounts_bd(
            login=input_data["login"],
            password=input_data["password"],
            token=input_data["token"],
            proxy=input_data["proxy"],
            user_id=user_id,
        )

        if input_data is None:
            return {
                "error": True,
                "ParserTypes": "Input data empty",
            }

        location = self.request.app.router["parser_request_accounts_template"].url_for()
        raise web.HTTPFound(location=location)
