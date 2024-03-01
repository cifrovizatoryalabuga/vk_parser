import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any
import inspect

import vk_api

from random import choice, randint
from time import sleep

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from vk_parser.admin.handlers.base import DependenciesMixin, CreateMixin
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


class ParserRequestDetailTemplateHandler(web.View, DependenciesMixin, CreateMixin):
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

        return {
            "parser_request": parser_request,
            "user_data": user_data,
        }

    def _get_id(self) -> int:
        try:
            return int(self.request.match_info["id"])
        except ValueError:
            raise HTTPBadRequest(reason="Invalid ID value")

    
    @aiohttp_jinja2.template("./parser_request/detail.html.j2")
    async def post(self) -> Mapping[str, Any]:
        
        counter_positive = 0
        counter_negative = 0
        token = "vk1.a.SdnKgAm9BcHgBSx9kDvNd1rS3cRwFBvTB2281aimNx3p4wQBUR6adJEGTI8pXaGYxEy5mokwaBeipOQApDzMr9CjMqhOmrvga4Y25opk4Fp2gDr_1pGZyO0gCYOobWoATHS0tCZ60OKpmiyO3HICZGInXepNDFn_ga3kQH6eFsJTJulu268H1X9P_U5bAb-a"
        vk_session = vk_api.VkApi(token=token)

        parser_request_id = self._get_id()
        
        parser_request = await self.parser_request_storage.get_detail(
            id_=parser_request_id,
        )
        if parser_request is None:
            raise HTTPNotFound
        if parser_request.parser_type == ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS:
            users = await self.vk_storage.get_users_by_parser_request_id(
                parser_request_id
            )

            for user in users:
                if counter_positive >= 10:
                    break
                else:
                    sleep(randint(20, 40))
                    try:
                        self.send_message_user(user.vk_user_id, vk_session)
                        counter_positive += 1
                        print(f"{counter_positive} : SUCCESSFUL MESSAGES!")
                    except TypeError as e:
                        print(e)
                        counter_negative += 1
                        print(f"{counter_negative} : ERRORS!")

        location = self.request.app.router["parser_request_send_messages_template"].url_for()
        raise web.HTTPFound(location=location)

    
    def send_message_user(self, user_id, vk_session):
        
        entry_words = ["Здравствуйте", "Доброго времени суток", "Привет", "Как дела", "Приветствую"]
        aim_words = ["проекте", "исследовании", "изучении", "направлении", "сборе информации"]
        names = ["Ангелина", "Ирина", "Ольга", "Анна", "Виолетта", "Галина"]

        random_symbols = ["q", 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l']
        
        try:
            vk_session.method('messages.send', {'user_id': user_id, 'message': f"{choice(entry_words)}, меня зовут {choice(names)}, я представитель НИИ РанХиГс. Мы проводим исследование на тему использования искусственного интеллекта на рабочем месте. Хотел бы узнать, как вы используете ИИ в своей работе и помогает ли он вам. Буду благодарена за ваше участие и помощь в нашем {choice(aim_words)}. {choice(random_symbols)}?", "random_id": 0})
        except vk_api.exceptions.ApiError as e:
            print(user_id, e)