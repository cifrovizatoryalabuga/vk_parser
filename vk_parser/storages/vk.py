from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

import sqlalchemy.dialects.postgresql as postgresql
from sqlalchemy import and_, cast, delete, insert, not_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.clients.vk import VkGroupMember, VkWallPost
from vk_parser.db.models.vk_group import VkGroup as VkGroupDb
from vk_parser.db.models.vk_group_post import VkGroupPost as VkGroupPostDb
from vk_parser.db.models.vk_group_user import VkGroupUser as VkGroupUserDb
from vk_parser.db.utils import inject_session
from vk_parser.generals.models.vk_group import VkGroup
from vk_parser.generals.models.vk_group_post import VkGroupPost
from vk_parser.generals.models.vk_group_user import VkGroupUser


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
                "vk_post_id": post.id,
                "vk_group_id": group_id,
                "posted_at": post.date_without_tz,
                "text": post.text,
                "user_vk_ids": post.user_vk_ids,
                "url": post.url,
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

    @inject_session
    async def remove_users_except(
        self,
        session: AsyncSession,
        ids: Iterable[int],
        group_id: int,
    ) -> None:
        query = delete(VkGroupUserDb).where(
            and_(
                VkGroupUserDb.vk_user_id.not_in(ids),
                VkGroupUserDb.vk_group_id == group_id,
            )
        )
        await session.execute(query)
        await session.commit()

    @inject_session
    async def get_group_user_ids(
        self,
        session: AsyncSession,
        group_id: int,
    ) -> Sequence[int]:
        query = select(VkGroupUserDb.vk_user_id).where(
            VkGroupUserDb.vk_group_id == group_id
        )
        result = await session.execute(query)
        return tuple(r[0] for r in result)

    @inject_session
    async def remove_posts_without_user_ids(
        self,
        session: AsyncSession,
        ids: Iterable[int],
        group_id: int,
    ) -> None:
        bigint_arr = cast(postgresql.array(ids), postgresql.ARRAY(postgresql.BIGINT))
        query = delete(VkGroupPostDb).where(
            and_(
                not_(VkGroupPostDb.user_vk_ids.overlap(bigint_arr)),
                VkGroupPostDb.vk_group_id == group_id,
            ),
        )
        await session.execute(query)
        await session.commit()

    @inject_session
    async def get_posts_by_parser_request_id(
        self,
        session: AsyncSession,
        parser_request_id: int,
    ) -> Sequence[VkGroupPost]:
        query = (
            select(VkGroupPostDb)
            .join(VkGroupDb, VkGroupDb.id == VkGroupPostDb.vk_group_id)
            .where(VkGroupDb.parser_request_id == parser_request_id)
        )
        res = await session.scalars(query)
        return [VkGroupPost.model_validate(row) for row in res]

    @inject_session
    async def get_users_by_parser_request_id(
        self,
        session: AsyncSession,
        parser_request_id: int,
    ) -> Sequence[VkGroupUser]:
        query = (
            select(VkGroupUserDb)
            .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
            .where(VkGroupDb.parser_request_id == parser_request_id)
            .order_by(VkGroupUserDb.created_at)
        )
        res = await session.scalars(query)
        return [VkGroupUser.model_validate(r) for r in res]


NType = TypeVar("NType", bound=Any)


def not_none(value: NType | None) -> NType:
    if value is None:
        raise ValueError
    return value
