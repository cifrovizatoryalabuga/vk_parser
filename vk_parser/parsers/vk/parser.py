import asyncio
import logging
from asyncio import gather
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.clients.vk import Vk, VkGroupMember, VkObjectType, VkWallPost
from vk_parser.generals.models.amqp import AmqpVkInputData
from vk_parser.generals.models.vk_group import VkGroup
from vk_parser.storages.parser_request import ParserRequestStorage
from vk_parser.storages.vk import VkStorage
from vk_parser.utils.parse import search_user_vk_ids

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VkParser:
    vk_client: Vk
    vk_storage: VkStorage
    parser_request_storage: ParserRequestStorage
    session_factory: async_sessionmaker[AsyncSession]

    async def process_request(self, input_data: AmqpVkInputData) -> None:
        try:
            await self._process(input_data=input_data)
        except ValueError as e:
            await self.parser_request_storage.save_error(
                id_=input_data.parser_request_id,
                finished_at=datetime.now(),
                error_message=str(e),
            )
            log.warning("Error processing with data: %s", input_data)

    async def _process(self, input_data: AmqpVkInputData) -> None:
        vk_group_id = await self._get_group_id(url=input_data.group_url)
        vk_group = await self.vk_storage.create_group(
            parser_request_id=input_data.parser_request_id,
            vk_id=vk_group_id,
            url=str(input_data.group_url),
        )
        tasks = gather(
            self._download_posts(
                vk_group=vk_group,
                posted_up_to=input_data.posted_up_to,
            ),
            self._download_users(
                vk_group=vk_group,
                max_age=input_data.max_age,
            ),
        )
        posts, users = await tasks
        if not posts or not users:
            await self._clear_all(group_id=vk_group.id)
            await self.parser_request_storage.save_empty_result(
                id_=input_data.parser_request_id,
                finished_at=datetime.now(),
                message="Empty group users"
                if not users
                else "Posts with users not found",
            )
            return
        log.info(
            "From group %d parsed %d posts and %d users",
            vk_group_id,
            len(posts),
            len(users),
        )

        users_in_posts = map_users_in_posts(posts)

        await self.vk_storage.remove_users(except_only=users_in_posts.keys())
        user_ids = await self.vk_storage.get_user_ids_by_group(group_id=vk_group.id)
        await self.vk_storage.remove_posts(except_with_user_ids=user_ids)

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
            if not chunk_posts:
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

    async def _clear_all(self, group_id: int) -> None:
        await self.vk_storage.clear_all_group(grop_id=group_id)


def map_users_in_posts(posts: Sequence[VkWallPost]) -> Mapping[int, int]:
    users_in_posts: dict[int, int] = {}
    for post in posts:
        for user_vk_id in post.user_vk_ids:
            users_in_posts[user_vk_id] = users_in_posts.get(user_vk_id, 0) + 1
    return users_in_posts
