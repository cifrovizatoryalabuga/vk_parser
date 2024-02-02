from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from vk_parser.admin.handlers.base import DependenciesMixin
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


class ParserRequestDetailTemplateHandler(web.View, DependenciesMixin):
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
