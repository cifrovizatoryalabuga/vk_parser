from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.clients.vk import VkGroupMember, VkWallPost
from vk_parser.db.models.vk_group import VkGroup as VkGroupDb
from vk_parser.db.models.vk_group_post import VkGroupPost as VkGroupPostDb
from vk_parser.db.models.vk_group_user import VkGroupUser as VkGroupUserDb
from vk_parser.db.utils import inject_session
from vk_parser.generals.models.vk_group import VkGroup


@dataclass(frozen=True, slots=True)
class VkStorage:
    session_factory: async_sessionmaker[AsyncSession]

    @inject_session
    async def create_group(
        self,
        session: AsyncSession,
        parser_request_id: int,
        vk_id: int,
        url: str,
    ) -> VkGroup:
        query = (
            insert(VkGroupDb)
            .values(
                parser_request_id=parser_request_id,
                vk_id=vk_id,
                url=url,
            )
            .returning(VkGroupDb)
        )
        obj = (await session.scalars(query)).one()
        await session.commit()
        return VkGroup.model_validate(obj)

    @inject_session
    async def create_posts(
        self,
        session: AsyncSession,
        posts: Sequence[VkWallPost],
        group_id: int,
    ) -> None:
        query = insert(VkGroupPostDb)
        insert_data = [
            {
                "vk_group_id": group_id,
                "posted_at": post.date_without_tz,
                "text": post.text,
                "user_vk_ids": post.user_vk_ids,
            }
            for post in posts
        ]
        await session.execute(query, insert_data)
        await session.commit()

    @inject_session
    async def create_users(
        self,
        session: AsyncSession,
        users: Sequence[VkGroupMember],
        group_id: int,
    ) -> None:
        query = insert(VkGroupUserDb)
        insert_data = [
            {
                "vk_group_id": group_id,
                "vk_user_id": user.id,
                "raw_data": user.model_dump(mode="json"),
                "birth_date": user.parsed_birth_date,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "last_visit_vk_date": user.last_visit_vk_date,
            }
            for user in users
        ]
        await session.execute(query, insert_data)
        await session.commit()
