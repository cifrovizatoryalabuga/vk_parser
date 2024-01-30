import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import ScalarResult, insert, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.db.models.parser_request import ParserRequest as ParserRequestDb
from vk_parser.db.utils import inject_session
from vk_parser.generals.enums import RequestStatus
from vk_parser.generals.models.pagination import PaginationResponse
from vk_parser.generals.models.parser_request import (
    DetailParserRequest,
    ParserRequest,
    ResultData,
)
from vk_parser.storages.base import PaginationMixin

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ParserRequestStorage(PaginationMixin):
    session_factory: async_sessionmaker[AsyncSession]

    async def get_pagination(
        self,
        page: int,
        page_size: int,
    ) -> PaginationResponse[ParserRequest]:
        query = select(ParserRequestDb)
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=ParserRequest,
        )

    @inject_session
    async def get_detail_parser_request_by_id(
        self,
        session: AsyncSession,
        id_: int,
    ) -> DetailParserRequest | None:
        query = select(ParserRequestDb).filter_by(id=id_)
        obj = (await session.scalars(query)).first()
        return DetailParserRequest.model_validate(obj) if obj else None

    @inject_session
    async def create(
        self,
        session: AsyncSession,
        input_data: Mapping[str, Any],
    ) -> DetailParserRequest | None:
        query = (
            insert(ParserRequestDb)
            .values(
                input_data=input_data,
            )
            .returning(ParserRequestDb)
        )
        try:
            result: ScalarResult[ParserRequestDb] = await session.scalars(query)
            await session.commit()
        except DBAPIError:
            log.warning(
                "Error in creating parser request: %s", input_data, exc_info=True
            )
            return None
        return DetailParserRequest.model_validate(result.one())

    @inject_session
    async def update_status(
        self,
        session: AsyncSession,
        id_: int,
        status: RequestStatus,
    ) -> DetailParserRequest | None:
        query = (
            update(ParserRequestDb)
            .where(ParserRequestDb.id == id_)
            .values(status=status)
            .returning(ParserRequestDb)
        )
        try:
            result = await session.scalars(query)
            await session.commit()
            return DetailParserRequest.model_validate(result.one())
        except DBAPIError as e:
            log.warning("Error updating error: %s", e)

        return None

    @inject_session
    async def save_error(
        self,
        session: AsyncSession,
        id_: int,
        finished_at: datetime,
        error_message: str,
    ) -> None:
        query = (
            update(ParserRequestDb)
            .where(ParserRequestDb.id == id_)
            .values(
                finished_at=finished_at,
                status=RequestStatus.FAILED,
                error_message=error_message,
            )
        )
        try:
            await session.execute(query)
            await session.commit()
        except DBAPIError:
            log.warning("Error save error")

    @inject_session
    async def save_empty_result(
        self,
        session: AsyncSession,
        id_: int,
        finished_at: datetime,
        message: str,
    ) -> None:
        query = (
            update(ParserRequestDb)
            .where(ParserRequestDb.id == id_)
            .values(
                finished_at=finished_at,
                status=RequestStatus.EMPTY,
                result_data={
                    "message": message,
                    "user_stat": [],
                },
            )
        )
        try:
            await session.execute(query)
            await session.commit()
        except DBAPIError:
            log.warning("Error save error")

    @inject_session
    async def save_successful_result(
        self,
        session: AsyncSession,
        id_: int,
        result_data: ResultData,
        finished_at: datetime,
    ) -> None:
        query = (
            update(ParserRequestDb)
            .where(ParserRequestDb.id == id_)
            .values(
                finished_at=finished_at,
                status=RequestStatus.SUCCESSFUL,
                result_data=result_data.model_dump(),
            )
        )
        try:
            await session.execute(query)
            await session.commit()
        except DBAPIError:
            log.warning("Error save error")
