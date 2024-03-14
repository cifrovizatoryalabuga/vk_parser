import logging
from asyncio import gather
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from operator import and_
from typing import Any
import datetime as dt

from aiohttp import web
from sqlalchemy import ScalarResult, delete, func, insert, select, update
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
