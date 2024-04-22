import asyncio
from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import jwt
from aiohttp import web
from aiomisc import timeout

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin
from vk_parser.generals.enums import SendMessageStatus


class SendMessageTemplateHandler(
    web.View,
    DependenciesMixin,
    ListMixin,
    CreateMixin,
):
    @aiohttp_jinja2.template("./parser_request/send_messages.html.j2")
    async def get(self) -> Mapping[str, Any]:
        jwt_token = self.request.cookies.get('jwt_token')
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)
            try:
                user = await self.auth_storage.get_user_by_login(decoded_jwt['login'])
                user_id = user.id
            except AttributeError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            params = self._parse()

            pagination = await self.parser_request_storage.send_messages_pagination_by_user(
                page=params.page,
                page_size=params.page_size,
                user_id=user_id,
            )
            return {
                "user_info": decoded_jwt,
                "pagination": pagination,
                "send_message_status": SendMessageStatus,
            }
        else:
            location = self.request.app.router["admin"].url_for()
            raise web.HTTPFound(location=location)

    @timeout(5)
    async def post(self) -> web.Response:
        input_data: str = await self.request.json()
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

        send_message_id = input_data["sendMessageId"]
        task_name = input_data["taskName"]
        for task in asyncio.all_tasks():
            if task.get_name() == task_name:
                task.cancel()
                await task
                await self.parser_request_storage.save_send_message_successful_result(
                    id_=int(send_message_id),
                )
                return web.Response(
                    text="<script>window.location.replace('/admin/all_users/');</script>",
                    content_type="text/html",
                    status=200,
                )

        await self.parser_request_storage.save_send_message_error_result(
            id_=int(send_message_id),
            error_message=f"Not found task: {task_name}",
        )
        return web.Response(
            text="<script>window.location.replace('/admin/all_users/');</script>",
            content_type="text/html",
            status=200,
        )
