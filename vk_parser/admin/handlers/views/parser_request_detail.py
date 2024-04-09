import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from random import choice
from typing import Any

import aiohttp_jinja2
import jwt
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
    university_name: str | None
    photo_100: str | None
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
            "to_user_year": self.request.query.get("to_user_year", None),
            "sex": self.request.query.get("sex", None),
        }
        parser_request = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )

        # Добавляем список городов со всех спаршенных Юзеров
        all_users = await self.vk_storage.get_users_by_parser_request_id(
            parser_request_id
        )
        all_cities = []
        for user in all_users:
            city = (user.city,)
            if city[0] not in all_cities:
                # Добавляем только уникальные города
                all_cities.append(city[0])

        if parser_request is None:
            raise HTTPNotFound
        user_data = None

        if parser_request.parser_type == ParserTypes.VK_SIMPLE_DOWNLOAD:
            params = self._parse()

            jwt_token = self.request.cookies.get("jwt_token")
            if jwt_token:
                try:
                    decoded_jwt = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
                except jwt.ExpiredSignatureError:
                    location = self.request.app.router["logout_user"].url_for()
                    raise web.HTTPFound(location=location)

                if (
                    response_data["city"]
                    and response_data["from_user_year"]
                    and response_data["to_user_year"]
                ):
                    users = (
                        await self.vk_storage.get_users_by_parser_request_id_advanced_filter(
                            parser_request_id,
                            city=response_data["city"],
                            from_user_year=response_data["from_user_year"],
                            to_user_year=response_data["to_user_year"],
                            sex=response_data["sex"],
                        )
                    )
                    pagination = await self.parser_request_storage.admin_pagination_users_advanced_filter(
                        parser_request_id,
                        page=params.page,
                        page_size=params.page_size,
                        filtered_city=response_data["city"],
                        filtered_year_from=response_data["from_user_year"],
                        filtered_year_to=response_data["to_user_year"],
                        filtered_sex=response_data["sex"],
                    )
                else:
                    users = await self.vk_storage.get_users_by_parser_request_id(
                        parser_request_id,
                    )
                    pagination = (
                        await self.parser_request_storage.admin_pagination_parsed_users(
                            parser_request_id,
                            page=params.page,
                            page_size=params.page_size,
                        )
                    )
                user_data = []
                for user in users:
                    user_data.append(user)

                return {
                    "users_data": user_data,
                    "user_info": decoded_jwt,
                    "response_data": response_data,
                    "pagination": pagination,
                    "parser_request": parser_request,
                    "user_data": user_data,
                    "all_cities": all_cities,
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
            "city": self.request.query.get("city", ""),
            "from_user_year": self.request.query.get("from_user_year", None),
            "to_user_year": self.request.query.get("to_user_year", None),
            "sex": self.request.query.get("sex", None),
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

        redirector_task = asyncio.create_task(
            self.parser_request_storage.redirector(url="/")
        )
        send_messages_task = asyncio.create_task(
            self.send_messages(
                parser_request_id,
                user_id,
                city=response_data["city"],
                from_user_year=response_data["from_user_year"],
                to_user_year=response_data["to_user_year"],
                sex=response_data["sex"],
            )
        )

        await asyncio.gather(redirector_task, send_messages_task)

        return None

    async def send_messages(
        self,
        parser_request_id: int,
        user_id: int,
        city: str,
        from_user_year: int,
        to_user_year: int,
        sex: str,
    ) -> None:
        users = await self.vk_storage.get_users_by_parser_request_id_advanced_filter(
            parser_request_id,
            city,
            from_user_year,
            to_user_year,
            sex,
        )
        async with ClientSession() as session:
            for user in users:
                try:
                    await self.send_message_to_user(session, user, user_id)
                except ConnectionError:
                    pass

                await asyncio.sleep(10)
        return None

    async def send_message_to_user(self, session, user: str, user_id: int) -> None:
        async with session.post(
            "https://api.vk.com/method/messages.send",
            params={
                "user_id": user.vk_user_id,
                "access_token": choice(
                    await self.parser_request_storage.get_random_account(user_id)
                ).secret_token,
                "message": choice(
                    await self.parser_request_storage.get_random_message(user_id)
                ).message,
                "random_id": 0,
                "v": "5.131",
            },
        ) as response:
            await response.json()

        return None
