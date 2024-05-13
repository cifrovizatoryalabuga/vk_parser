import asyncio
from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import jwt
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin
from vk_parser.admin.message_sender import MessageSender


class ParserRequestDetailTemplateHandler(web.View, DependenciesMixin, CreateMixin, ListMixin):
    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def get(self) -> Mapping[str, Any]:
        parser_request_id = self._get_id()
        parser_request = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )

        if parser_request is None:
            raise HTTPNotFound

        response_data = {
            "city": self.request.query.get("city", "all_cities"),
            "from_user_year": self.request.query.get("from_user_year", 1900),
            "to_user_year": self.request.query.get("to_user_year", 2024),
            "sex": self.request.query.get("sex", "all_sex"),
        }

        users = await self.vk_storage.get_users_by_parser_request_id(parser_request_id)
        cities = set(user.city for user in users if user.city)

        jwt_token = self.request.cookies.get("jwt_token")

        if jwt_token:
            try:
                jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            params = self._parse()
            pagination = await self.parser_request_storage.admin_pagination_users_advanced_filter(
                parser_request_id,
                page=params.page,
                page_size=params.page_size,
                filtered_city=str(response_data["city"]),
                filtered_year_from=str(response_data["from_user_year"]),
                filtered_year_to=str(response_data["to_user_year"]),
                filtered_sex=str(response_data["sex"]),
            )

            vk_user_ids = [item.vk_user_id for item in pagination.items]

            posts = [
                await self.vk_storage.get_posts_by_user_vk_id(
                    user_vk_id=vk_user_id,
                    parser_request_id=parser_request_id,
                )
                for vk_user_id in vk_user_ids
            ]

            pagination.items = list(zip(pagination.items, posts))

            return {
                "posts": posts,
                "response_data": response_data,
                "pagination": pagination,
                "parser_request": parser_request,
                "cities": cities,
            }
        else:
            location = self.request.app.router["admin"].url_for()
            raise web.HTTPFound(location=location)

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")

    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def post(self) -> None:
        parser_request_id = self._get_id()
        response_data = {
            "city": self.request.query.get("city", "all_cities"),
            "from_user_year": self.request.query.get("from_user_year", 1900),
            "to_user_year": self.request.query.get("to_user_year", 2024),
            "sex": self.request.query.get("sex", "all_sex"),
        }
        jwt_token = self.request.cookies.get("jwt_token")
        if jwt_token:
            try:
                decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                location = self.request.app.router["logout_user"].url_for()
                raise web.HTTPFound(location=location)

            user = await self.auth_storage.get_user_by_login(decoded_jwt["login"])
            user_id = user.id

        users = await self.vk_storage.get_users_by_parser_request_id_advanced_filter(
            parser_request_id,
            city=str(response_data["city"]),
            from_user_year=int(response_data["from_user_year"]),
            to_user_year=int(response_data["to_user_year"]),
            sex=str(response_data["sex"]),
        )

        redirector_task = asyncio.create_task(self.parser_request_storage.redirector(url="/admin/send_messages/"))

        message_sender = MessageSender()
        send_messages_task = message_sender.start_send_messages_task(
            user_id=user_id,
            parser_request_id=parser_request_id,
            users=users,
        )

        await asyncio.gather(redirector_task, send_messages_task)

        return None
