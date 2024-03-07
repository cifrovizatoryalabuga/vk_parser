import asyncio
import logging
from asyncio import gather
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import HttpUrl

from vk_parser.clients.vk import Vk, VkGroupMember, VkObjectType, VkWallPost
from vk_parser.generals.enums import RequestMessage
from vk_parser.generals.models.parser_request import (
    ParsePostsVkForm,
    Result,
    SimpleVkForm,
    UserStat,
)
from vk_parser.generals.models.vk_group import VkGroup
from vk_parser.parsers.base import BaseParser, BaseSender
from vk_parser.storages.parser_request import ParserRequestStorage
from vk_parser.storages.vk import VkStorage
from vk_parser.utils.parsers import map_users_in_posts, search_user_vk_ids

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PostVkParser(BaseParser):
    vk_client: Vk
    vk_storage: VkStorage
    parser_request_storage: ParserRequestStorage

    async def _process(
        self, parser_request_id: int, input_data: dict[str, Any]
    ) -> None:
        data = ParsePostsVkForm(**input_data)
        vk_group_id = await self._get_group_id(url=data.group_url)
        vk_group = await self.vk_storage.create_group(
            parser_request_id=parser_request_id,
            vk_id=vk_group_id,
            url=str(data.group_url),
        )
        tasks = gather(
            self._download_posts(
                vk_group=vk_group,
                posted_up_to=data.posted_up_to,
            ),
            self._download_users(
                vk_group=vk_group,
                max_age=data.max_age,
            ),
        )
        posts, users = await tasks
        if not posts or not users:
            await self._save_empty_result(
                parser_request_id=parser_request_id,
                message=RequestMessage.EMPTY_USERS
                if not users
                else RequestMessage.EMPTY_POSTS,
            )
            return
        log.info(
            "From group %d parsed %d posts and %d users",
            vk_group_id,
            len(posts),
            len(users),
        )
        users_in_posts = map_users_in_posts(posts)
        await self.vk_storage.remove_users_except(
            ids=users_in_posts.keys(),
            group_id=vk_group.id,
        )
        user_ids = await self.vk_storage.get_group_user_ids(group_id=vk_group.id)
        if not user_ids:
            await self._save_empty_result(
                parser_request_id=parser_request_id,
                message=RequestMessage.EMPTY_INTERSECTION,
            )
            return
        await self.vk_storage.remove_posts_without_user_ids(
            ids=user_ids,
            group_id=vk_group.id,
        )

        result = await self._calculate_result(user_ids, users_in_posts)
        await self._save_successful_result(
            parser_request_id=parser_request_id,
            result=result,
        )

    async def _get_group_id(self, url: HttpUrl) -> int:
        if url.path is None:
            raise ValueError("Can't parse group ID")
        resolved_object = await self.vk_client.resolve_screen_name(url.path[1:])
        if not resolved_object:
            log.info("Got resolved object: %s", resolved_object)
            raise ValueError("Can't parse group ID")
        if resolved_object.type != VkObjectType.GROUP:
            raise ValueError("Sent url is not group URL")

        return resolved_object.object_id

    async def _download_posts(
        self, vk_group: VkGroup, posted_up_to: datetime
    ) -> Sequence[VkWallPost]:
        posted_up_to_without_tz = posted_up_to.replace(tzinfo=None)
        posts: list[VkWallPost] = []
        offset = 0
        do_next = True
        while do_next:
            chunk_posts = await self.vk_client.get_group_posts(
                group_id=vk_group.vk_id,
                offset=offset,
            )
            if not chunk_posts or not chunk_posts.items:
                do_next = False
                break
            for post in chunk_posts.items:
                if post.date_without_tz < posted_up_to_without_tz:
                    do_next = False
                    break
                user_vk_ids = search_user_vk_ids(post.text)
                if not user_vk_ids:
                    continue
                post.user_vk_ids = user_vk_ids
                posts.append(post)
            offset += len(chunk_posts.items)
            await asyncio.sleep(0.2)

        if posts:
            await self.vk_storage.create_posts(posts, vk_group.id)
        return posts

    async def _download_users(
        self,
        vk_group: VkGroup,
        max_age: int,
    ) -> Sequence[VkGroupMember]:
        users: list[VkGroupMember] = []
        offset = 0
        do_next = True
        while do_next:
            chunk_users = await self.vk_client.get_group_members(
                group_id=vk_group.vk_id,
                offset=offset,
            )
            if not chunk_users:
                do_next = False
                break
            for user in chunk_users.items:
                if user.in_age_range(max_age=max_age):
                    users.append(user)
            offset += len(chunk_users.items)
            if offset >= chunk_users.count:
                break
            await asyncio.sleep(0.3)
        if users:
            await self.vk_storage.create_users(users, vk_group.id)
        return users

    async def _calculate_result(
        self, user_ids: Sequence[int], users_in_posts: Mapping[int, int]
    ) -> Result:
        user_ids_set = set(user_ids)
        user_stat = []
        for id_ in users_in_posts:
            if id_ in user_ids_set:
                user_stat.append(UserStat(vk_id=id_, count=users_in_posts[id_]))
        return Result(message="Successful finished", user_stat=user_stat)


@dataclass(frozen=True, slots=True)
class SimpleVkParser(BaseParser):
    vk_client: Vk
    vk_storage: VkStorage
    parser_request_storage: ParserRequestStorage

    async def _process(
        self, parser_request_id: int, input_data: dict[str, Any]
    ) -> None:
        data = SimpleVkForm(**input_data)
        vk_group_id = await self._get_group_id(url=data.group_url)
        vk_group = await self.vk_storage.create_group(
            parser_request_id=parser_request_id,
            vk_id=vk_group_id,
            url=str(data.group_url),
        )
        users = await self._download_users(
            vk_group=vk_group,
            max_age=data.max_age,
        )

        if not users:
            await self.parser_request_storage.save_empty_result(
                id_=parser_request_id,
                finished_at=datetime.now(),
                message="Empty group users"
                if not users
                else "Posts with users not found",
            )
            return
        log.info(
            "From group %d parsed %d users",
            vk_group_id,
            len(users),
        )

        await self.parser_request_storage.save_successful_result(
            id_=parser_request_id,
            result=Result(message="Successful finished", user_stat=[]),
            finished_at=datetime.now(),
        )

    async def _get_group_id(self, url: HttpUrl) -> int:
        path = url.path
        if path is None:
            raise ValueError("Can't parse group ID")
        resolved_object = await self.vk_client.resolve_screen_name(path[1:])
        if not resolved_object:
            log.info("Got resolved object: %s", resolved_object)
            raise ValueError("Can't parse group ID")
        if resolved_object.type != VkObjectType.GROUP:
            raise ValueError("Sent url is not group URL")

        return resolved_object.object_id

    async def _download_users(
        self,
        vk_group: VkGroup,
        max_age: int,
    ) -> Sequence[VkGroupMember]:
        users: list[VkGroupMember] = []
        offset = 0
        do_next = True
        while do_next:
            chunk_users = await self.vk_client.get_group_members(
                group_id=vk_group.vk_id,
                offset=offset,
            )
            if not chunk_users:
                do_next = False
                break
            for user in chunk_users.items:
                if user.in_age_range(max_age=max_age):
                    users.append(user)
            offset += len(chunk_users.items)
            if offset >= chunk_users.count:
                break
            await asyncio.sleep(0.3)
        if users:
            await self.vk_storage.create_users(users, vk_group.id)
        return users


@dataclass(frozen=True, slots=True)
class SendMessages(BaseSender):
    vk_client: Vk
    vk_storage: VkStorage
    parser_request_storage: ParserRequestStorage

    async def _process(
        self, parser_request_id: int, input_data: dict[str, Any]
    ) -> None:
        pass
