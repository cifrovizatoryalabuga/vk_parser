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
    sex: int | None
    city: dict | None
    last_visit_vk_date: date | None
    posts: list[PostData] = field(default_factory=list)

@dataclass
class UserCities:
    city: str | None

class ParserRequestDetailTemplateHandler(
    web.View, DependenciesMixin, CreateMixin, ListMixin
):
    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def get(self) -> Mapping[str, Any]:
        parser_request_id = self._get_id()
        response_data = {
            "city": self.request.query.get("city", ""),
            "from_user_year": self.request.query.get("from_user_year", None),
            "to_user_year": self.request.query.get("to_user_year", None)
        }
        print(response_data)
        parser_request = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )

        # Добавляем список городов со всех спаршенных Юзеров
        all_users = await self.vk_storage.get_users_by_parser_request_id(
                parser_request_id
            )
        all_cities = []
        for user in all_users:
            city = user.city,
            if city[0] not in all_cities:
                #Добавляем только уникальные города
                all_cities.append(city[0])

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
                    sex=user.sex,
                    city=user.city,
                    birth_date=user.birth_date,
                    last_visit_vk_date=user.last_visit_vk_date,
                )
                for post in posts:
                    if user.vk_user_id in post.user_vk_ids:
                        row.posts.append(PostData(url=post.url, text=post.text[:300]))
                user_data.append(row)

        elif parser_request.parser_type == ParserTypes.VK_SIMPLE_DOWNLOAD:
            if response_data["city"] and response_data["from_user_year"] and response_data["to_user_year"]:
                print(1)
                users = await self.vk_storage.get_users_by_parser_request_id_filtered(
                    parser_request_id,
                    filtered_city=response_data['city'],
                    filtered_year_from=response_data['from_user_year'],
                    filtered_year_to=response_data['to_user_year'],
                )
            else:
                users = await self.vk_storage.get_users_by_parser_request_id(
                    parser_request_id,
                )
            user_data = []
            for user in users:
                row = UserRow(
                    vk_user_id=user.vk_user_id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    sex=user.sex,
                    city=user.city,
                    birth_date=user.birth_date,
                    last_visit_vk_date=user.last_visit_vk_date,
                )
                user_data.append(row)

        params = self._parse()

        pagination = await self.parser_request_storage.admin_pagination_parsed_users(
            parser_request_id,
            page=params.page,
            page_size=params.page_size,
        )

        return {
            "response_data": response_data,
            "pagination": pagination,
            "parser_request": parser_request,
            "user_data": user_data,
            "all_cities": all_cities,
        }

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")


    @aiohttp_jinja2.template("./parser_request/detail.html.j2")  # type: ignore
    async def post(self) -> None:  # type: ignore
        parser_request_id = self._get_id()

        redirector_task = asyncio.create_task(
            self.parser_request_storage.redirector(url="/")
        )
        send_messages_task = asyncio.create_task(self.send_messages(parser_request_id))

        await asyncio.gather(redirector_task, send_messages_task)

        return None

    async def send_messages(self, parser_request_id: int) -> None:
        users = await self.vk_storage.get_users_by_parser_request_id(parser_request_id)
        print(users)
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
