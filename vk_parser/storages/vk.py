import datetime as dt
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from random import choice
from typing import Any, TypeVar, List

import sqlalchemy.dialects.postgresql as postgresql
from sqlalchemy import and_, cast, delete, insert, not_, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.clients.vk import VkGroupMember, VkWallPost
from vk_parser.db.models.parser_request import ParserRequest as ParserRequestDb
from vk_parser.db.models.vk_group import VkGroup as VkGroupDb
from vk_parser.db.models.vk_group_post import VkGroupPost as VkGroupPostDb
from vk_parser.db.models.vk_group_user import VkGroupUser as VkGroupUserDb
from vk_parser.db.models.vk_user_messanger import MAX_SUCCESSFUL_MESSAGES
from vk_parser.db.models.vk_user_messanger import Messages as MessagesDb
from vk_parser.db.models.vk_user_messanger import SendAccounts as SendAccountsDb
from vk_parser.db.utils import inject_session
from vk_parser.generals.enums import SendAccountStatus
from vk_parser.generals.models.vk_group import VkGroup
from vk_parser.generals.models.vk_group_post import VkGroupPost
from vk_parser.generals.models.vk_group_user import VkGroupUser
from vk_parser.generals.models.vk_user_messanger import Messages

log = logging.getLogger(__name__)


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
        parser_request_id: int,
    ) -> None:
        query = insert(VkGroupUserDb)
        insert_data = [
            {
                "parser_request_id": parser_request_id,
                "photo_100": user.photo_100,
                "vk_group_id": group_id,
                "vk_user_id": user.id,
                "raw_data": user.model_dump(mode="json"),
                "birth_date": user.parsed_birth_date,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "sex": sex_convert_vk(user.sex),
                "mobile_phone": user.mobile_phone,
                "home_phone": user.home_phone,
                "university_name": user.university_name,
                "city": city_convert_vk(user.city),
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
    async def remove_users_by_id(self, session: AsyncSession, id: int, parser_request_id: int) -> None:
        try:
            query = delete(VkGroupUserDb).where(
                and_(
                    VkGroupUserDb.vk_user_id == id,
                    VkGroupUserDb.parser_request_id == parser_request_id,
                )
            )
            await session.execute(query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @inject_session
    async def get_parser_by_auth_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Sequence[ParserRequestDb]:
        try:
            query = (
                select(ParserRequestDb)
                .where(ParserRequestDb.user_id == user_id)
                .order_by(ParserRequestDb.created_at.desc())
            )
            res = await session.scalars(query)
            return res.fetchall()
        except Exception as e:
            await session.rollback()
            raise e

    @inject_session
    async def remove_parser_by_id(
        self,
        session: AsyncSession,
        id: int,
    ) -> None:
        try:
            query = delete(ParserRequestDb).where(
                ParserRequestDb.id == id,
            )
            await session.execute(query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @inject_session
    async def update_successful_messages_by_id(
        self,
        session: AsyncSession,
        account_id: int,
    ) -> None:
        try:
            account = await session.execute(
                select(SendAccountsDb).where(SendAccountsDb.id == account_id),
            )
            account = account.scalars().first()

            account.successful_messages += 1

            if account.successful_messages >= MAX_SUCCESSFUL_MESSAGES:
                account.status = SendAccountStatus.INACTIVE

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @inject_session
    async def get_group_user_ids(
        self,
        session: AsyncSession,
        group_id: int,
    ) -> Sequence[int]:
        query = select(VkGroupUserDb.vk_user_id).where(VkGroupUserDb.vk_group_id == group_id)
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
    async def get_posts_by_user_vk_id(
        self,
        session: AsyncSession,
        user_vk_id: int,
        parser_request_id: int,
    ) -> Sequence[VkGroupPost]:
        query = (
            select(VkGroupPostDb)
            .join(VkGroupDb, VkGroupDb.id == VkGroupPostDb.vk_group_id)
            .where(
                VkGroupPostDb.user_vk_ids.any(user_vk_id),
                VkGroupDb.parser_request_id == parser_request_id
            )
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
        )
        res = await session.scalars(query)
        return [VkGroupUser.model_validate(r) for r in res]

    @inject_session
    async def get_users_by_parser_request_id_advanced_filter(
        self,
        session: AsyncSession,
        parser_request_id: int,
        city: str | None = None,
        from_user_year: int | None = None,
        to_user_year: int | None = None,
        sex: str | None = None,
    ) -> Sequence[VkGroupUser]:
        query = (
            select(VkGroupUserDb)
            .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
            .where(VkGroupDb.parser_request_id == parser_request_id)
        )

        if city is not None:
            if city == "None":
                query = query.filter(VkGroupUserDb.city.is_(None))
            elif city != "all_cities":
                query = query.filter(VkGroupUserDb.city == city)
        if from_user_year is not None:
            from_date = dt.datetime.strptime(f"01.01.{from_user_year}", "%d.%m.%Y")
            query = query.filter(VkGroupUserDb.birth_date >= from_date)
        if to_user_year is not None:
            to_date = dt.datetime.strptime(f"01.01.{to_user_year}", "%d.%m.%Y")
            query = query.filter(VkGroupUserDb.birth_date <= to_date)
        if sex is not None and sex != "all_sex":
            query = query.filter(VkGroupUserDb.sex == sex)

        res = await session.scalars(query)
        return [VkGroupUser.model_validate(r) for r in res]

    @inject_session
    async def get_users_by_parser_request_id_filtered(
        self,
        session: AsyncSession,
        parser_request_id: int,
        filtered_city: str | None,
        filtered_year_from: str,
        filtered_year_to: str,
    ) -> Sequence[VkGroupUser]:
        if filtered_city != "all_cities":
            if filtered_city == "None":
                filtered_city = None
            query = (
                select(VkGroupUserDb)
                .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
                .where(
                    and_(VkGroupDb.parser_request_id == parser_request_id),
                    (VkGroupUserDb.city == filtered_city),
                    (VkGroupUserDb.birth_date >= dt.datetime.strptime(f"01.01.{filtered_year_from}", "%d.%m.%Y")),
                    (VkGroupUserDb.birth_date <= dt.datetime.strptime(f"01.01.{filtered_year_to}", "%d.%m.%Y")),
                )
            )
            res = await session.scalars(query)
            return [VkGroupUser.model_validate(r) for r in res]
        else:
            query = (
                select(VkGroupUserDb)
                .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
                .where(
                    and_(
                        VkGroupDb.parser_request_id == parser_request_id,
                        VkGroupUserDb.birth_date >= dt.datetime.strptime(f"01.01.{filtered_year_from}", "%d.%m.%Y"),
                        VkGroupUserDb.birth_date <= dt.datetime.strptime(f"01.01.{filtered_year_to}", "%d.%m.%Y"),
                    )
                )
            )
            res = await session.scalars(query)
            return [VkGroupUser.model_validate(r) for r in res]

    @inject_session
    async def add_accounts_bd(
        self,
        session: AsyncSession,
        login: str,
        password: str,
        token: str,
        proxy: str,
        user_id: int,
    ) -> None:
        query = insert(SendAccountsDb)
        try:
            insert_data = {
                "user_id": user_id,
                "login": login,
                "password": password,
                "secret_token": token,
                "proxy": proxy,
                "successful_messages": 0,
                "error_status": "no_error",
                "user_link": "vk.com/workwork",
                "expire_timestamp": "01.02.2000",
            }

            await session.execute(query, insert_data)
            await session.commit()
        except IntegrityError:
            log.warning(
                "Error in creating account! Duplicate account: %s",
                insert_data,
                exc_info=True,
            )
            return "Duplicate"

        except DBAPIError:
            log.warning(
                "Error in creating account! Incorrect form account: %s",
                insert_data,
                exc_info=True,
            )
            return None
        return None

    @inject_session
    async def add_messages_bd(
        self,
        session: AsyncSession,
        message: str,
        order: int,
        user_id: int,
    ) -> Messages:
        query = (
            insert(MessagesDb)
            .values(
                user_id=user_id,
                order=int(order),
                message=message,
            )
            .returning(MessagesDb)
        )
        obj = (await session.scalars(query)).one()
        await session.commit()
        return Messages.model_validate(obj)

    @inject_session
    async def get_random_account(
        self,
        session: AsyncSession,
    ) -> str:
        query = select(SendAccountsDb)
        res = await session.scalars(query)
        return choice(res)

    @inject_session
    async def get_random_message(
        self,
        session: AsyncSession,
    ) -> str:
        query = select(MessagesDb)
        res = await session.scalars(query)
        return choice(res)


NType = TypeVar("NType", bound=Any)


def not_none(value: NType | None) -> NType:
    if value is None:
        raise ValueError
    return value


def sex_convert_vk(sex: int) -> str | None:
    if sex == 1:
        return "Ж"
    elif sex == 2:
        return "М"
    else:
        return None


def city_convert_vk(city: dict[str, Any]) -> str | None:
    if city is not None:
        try:
            return city["title"]
        except KeyError:
            return None
    else:
        return None


def show_item(item):
    print(item)
    return item
