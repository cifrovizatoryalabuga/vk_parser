import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from random import choice
from typing import Any

import aiohttp_jinja2
from aiohttp import ClientSession, web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin, ListMixin
from vk_parser.generals.enums import ParserTypes


@dataclass
class PostData:
    url: str
    text: str


@dataclass
class UserRow:
    vk_user_id: int
    first_name: str | None
    last_name: str | None
    birth_date: date | None
    last_visit_vk_date: date | None
    posts: list[PostData] = field(default_factory=list)


class ParserRequestDetailTemplateHandler(
    web.View, DependenciesMixin, CreateMixin, ListMixin
):
    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def get(self) -> Mapping[str, Any]:
        parser_request_id = self._get_id()
        parser_request = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )
        if parser_request is None:
            raise HTTPNotFound
        user_data = None
        if parser_request.parser_type == ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS:
            users = await self.vk_storage.get_users_by_parser_request_id(
                parser_request_id
            )
            posts = await self.vk_storage.get_posts_by_parser_request_id(
                parser_request_id
            )
            user_data = []
            for user in users:
                row = UserRow(
                    vk_user_id=user.vk_user_id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    birth_date=user.birth_date,
                    last_visit_vk_date=user.last_visit_vk_date,
                )
                for post in posts:
                    if user.vk_user_id in post.user_vk_ids:
                        row.posts.append(PostData(url=post.url, text=post.text[:300]))
                user_data.append(row)

        elif parser_request.parser_type == ParserTypes.VK_SIMPLE_DOWNLOAD:
            users = await self.vk_storage.get_users_by_parser_request_id(
                parser_request_id
            )
            user_data = []
            for user in users:
                row = UserRow(
                    vk_user_id=user.vk_user_id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    birth_date=user.birth_date,
                    last_visit_vk_date=user.last_visit_vk_date,
                )
                user_data.append(row)

        params = self._parse()

        pagination = await self.parser_request_storage.admin_pagination_parsed_users(
            parser_request_id=parser_request_id,
            page=params.page,
            page_size=params.page_size,
        )

        return {
            "pagination": pagination,
            "parser_request": parser_request,
            "user_data": user_data,
        }

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")

    @aiohttp_jinja2.template("./parser_request/detail.html.j2")  # type: ignore
    async def post(self) -> None:  # type: ignore
        parser_request_id = self._get_id()

        # Создаем задачи для редиректа и отправки сообщений
        redirector_task = asyncio.create_task(
            self.parser_request_storage.redirector(url="/")
        )
        send_messages_task = asyncio.create_task(self.send_messages(parser_request_id))

        # Ожидаем выполнение редиректа и отправки сообщений
        await asyncio.gather(redirector_task, send_messages_task)

        return None

    async def send_messages(self, parser_request_id: int) -> None:
        users = await self.vk_storage.get_users_by_parser_request_id(parser_request_id)
        async with ClientSession() as session:
            for user in users:
                try:
                    await self.send_message_to_user(session, user)  # type: ignore
                except ConnectionError:
                    pass

                await asyncio.sleep(10)
        return None

    async def send_message_to_user(self, session, user: str) -> None:  # type: ignore
        async with session.post(
            "https://api.vk.com/method/messages.send",
            params={
                "user_id": user.vk_user_id,  # type: ignore
                "access_token": choice(
                    await self.parser_request_storage.get_random_account()
                ).secret_token,
                "message": choice(
                    await self.parser_request_storage.get_random_message()
                ).message,
                "random_id": 0,
                "v": "5.131",
            },
        ) as response:
            await response.json()
            print(response)

        return None
