import logging
from asyncio import gather
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from operator import and_
from typing import Any
import datetime as dt

from aiohttp import web
from sqlalchemy import ScalarResult, delete, func, insert, select, update, create_engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.db.models.auth import AuthUser as AuthUserDb
from vk_parser.db.utils import inject_session
from vk_parser.generals.models.auth import (
    AuthUser
)
from vk_parser.generals.models.pagination import PaginationResponse
from vk_parser.storages.base import PaginationMixin

log = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class AuthorizationStorage(PaginationMixin):
    session_factory: async_sessionmaker[AsyncSession]

    @inject_session
    async def create(
        self,
        session: AsyncSession,
        input_data: Mapping[str, Any],
    ) -> AuthUser | None:
        query = insert(AuthUserDb).values(input_data).returning(AuthUserDb)
        try:
            await session.execute(query, input_data)
            await session.commit()

        except IntegrityError:
            log.warning(
                    "Error in creating user! Duplicate user: %s", input_data, exc_info=True
                )
            return "Duplicate"

        except DBAPIError:
            log.warning(
                    "Error in creating user! Incorrect form user: %s", input_data, exc_info=True
                )
            return None
        return None


    async def paginate_users(
        self,
        page: int,
        page_size: int,
    ) -> PaginationResponse[AuthUser]:
        query = select(AuthUserDb).order_by(AuthUserDb.created_at.desc())

        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=AuthUser,
        )

    @inject_session
    async def authorization_user(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> bool:

        count_query = select(func.count()).select_from(AuthUserDb).where(
        and_(
            (AuthUserDb.login == login),
            (AuthUserDb.password == password),
        )
    )

        result = await session.execute(count_query)
        count = result.scalar()

        return count

    @inject_session
    async def get_user_by_login(
        self,
        session: AsyncSession,
        login: str,
    ) -> bool:

        count_query = select(AuthUserDb).where(AuthUserDb.login == login)

        result = await session.execute(count_query)

        user = result.scalar_one_or_none()  # Получаем один объект или None

        if user:  # Если пользователь найден
            return user  # Возвращаем значение поля role
        else:
            return None  # Или что-то другое, в зависимости от логики вашего приложения

    @inject_session
    async def remove_users_by_id(self, session: AsyncSession, id: int) -> None:
        try:
            query = delete(AuthUserDb).where(AuthUserDb.id == id)

            await session.execute(query)
            await session.commit()

        except Exception as e:
            await session.rollback()
            raise e

    @inject_session
    async def change_role(self, session: AsyncSession, user_id: int, role: str) -> None:
        try:
            # Получаем объект пользователя по его ID
            user = await session.execute(select(AuthUserDb).where(AuthUserDb.id == user_id))
            user = user.scalars().first()

            # Обновляем поле роли
            user.role = role

            # Коммит изменений в базе данных
            await session.commit()

        except Exception as e:
            await session.rollback()
            raise e

    @inject_session
    async def get_all_users(self, session: AsyncSession) -> None:
        try:
            # Получаем объект пользователя по его ID
            users = await session.execute(select(AuthUserDb))
            users = users.scalars()

            # Коммит изменений в базе данных
            await session.commit()

            return users

        except Exception as e:
            await session.rollback()
            raise e


    @inject_session
    async def get_users_by_role_filtered(
        self,
        session: AsyncSession,
        role: str,
    ) -> Sequence[AuthUserDb]:
        if role != "all_roles":
            if filtered_city == "None":
                filtered_city = None
            query = (
                select(AuthUserDb)
                .where(AuthUserDb.role == role)
                .order_by(AuthUserDb.created_at)
            )
            res = await session.scalars(query)
            print(res)
            return [AuthUserDb.model_validate(r) for r in res]
        else:
            query = (
                select(AuthUserDb)
                .order_by(AuthUserDb.created_at)
            )
            res = await session.scalars(query)
            return [AuthUserDb.model_validate(r) for r in res]

    async def paginate_filtered_users(
        self,
        page: int,
        page_size: int,
        role: str,
    ) -> PaginationResponse[AuthUser]:
        if role != "all_roles":
            query = (
                select(AuthUserDb)
                .where(AuthUserDb.role == role)
                .order_by(AuthUserDb.created_at)
            )
        else:
            query = (
                select(AuthUserDb)
                .order_by(AuthUserDb.created_at)
            )

        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=AuthUser,
        )
