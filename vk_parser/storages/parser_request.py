import datetime as dt
import logging
from asyncio import gather
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiohttp import web
from sqlalchemy import ScalarResult, delete, func, insert, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.db.models.parser_request import ParserRequest as ParserRequestDb
from vk_parser.db.models.send_message import SendMessages as SendMessagesDb
from vk_parser.db.models.vk_group import VkGroup as VkGroupDb
from vk_parser.db.models.vk_group_user import VkGroupUser as VkGroupUserDb
from vk_parser.db.models.vk_messages import VkDialogs as VkDialogsDb
from vk_parser.db.models.vk_messages import VkMessages as VkMessagesDb
from vk_parser.db.models.vk_user_messanger import Messages as MessagesDb
from vk_parser.db.models.vk_user_messanger import SendAccounts as SendAccountsDb
from vk_parser.db.utils import inject_session
from vk_parser.generals.enums import (
    ParserTypes,
    RequestStatus,
    SendAccountStatus,
    SendMessageStatus,
)
from vk_parser.generals.models.pagination import PaginationResponse
from vk_parser.generals.models.parser_request import (
    DetailParserRequest,
    ParserRequest,
    Result,
)
from vk_parser.generals.models.send_message import SendMessages
from vk_parser.generals.models.vk_group_user import VkGroupUser
from vk_parser.generals.models.vk_messages import VkDialogs, VkMessages
from vk_parser.generals.models.vk_user_messanger import Messages, SendAccounts
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

    async def get_pagination_accounts(
        self,
        page: int,
        page_size: int,
    ) -> PaginationResponse[SendAccounts]:
        query = select(SendAccountsDb)
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=SendAccounts,
        )

    @inject_session
    async def delete_messages(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> None:
        query = delete(MessagesDb).where(MessagesDb.user_id == user_id)
        await session.execute(query)
        await session.commit()

    @inject_session
    async def delete_accounts(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> None:
        await session.execute(
            update(SendAccountsDb)
            .where(SendAccountsDb.user_id == user_id)
            .where(SendAccountsDb.status == SendAccountStatus.INACTIVE)
            .values(status=SendAccountStatus.ARCHIVE)
        )

        await session.execute(
            delete(SendAccountsDb)
            .where(SendAccountsDb.user_id == user_id)
            .where(SendAccountsDb.status != SendAccountStatus.INACTIVE)
        )

        await session.commit()

    async def admin_pagination_by_user(
        self,
        page: int,
        page_size: int,
        user_id: int,
    ) -> PaginationResponse[DetailParserRequest]:
        query = (
            select(ParserRequestDb)
            .where(ParserRequestDb.user_id == user_id)
            .order_by(ParserRequestDb.created_at.desc())
        )
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=DetailParserRequest,
        )

    async def send_messages_pagination_by_user(
        self,
        page: int,
        page_size: int,
        user_id: int,
    ) -> PaginationResponse[SendMessages]:
        query = (
            select(SendMessagesDb).where(SendMessagesDb.user_id == user_id).order_by(SendMessagesDb.created_at.desc())
        )
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=SendMessages,
        )

    async def admin_pagination(
        self,
        page: int,
        page_size: int,
    ) -> PaginationResponse[DetailParserRequest]:
        query = select(ParserRequestDb).order_by(ParserRequestDb.created_at.desc())
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=DetailParserRequest,
        )

    async def admin_pagination_filtered(
        self,
        page: int,
        page_size: int,
        user_id: str,
    ) -> PaginationResponse[DetailParserRequest]:
        if user_id != "all_parsers":
            query = (
                select(ParserRequestDb)
                .where(ParserRequestDb.user_id == user_id)
                .order_by(ParserRequestDb.created_at.desc())
            )
        else:
            query = select(ParserRequestDb).order_by(ParserRequestDb.created_at.desc())
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=DetailParserRequest,
        )

    async def admin_pagination_accounts(
        self,
        page: int,
        page_size: int,
        user_id: int,
    ) -> PaginationResponse[SendAccounts]:
        query = select(SendAccountsDb).where(SendAccountsDb.user_id == user_id)
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=SendAccounts,
        )

    async def admin_pagination_parsed_users(
        self,
        parser_request_id: int,
        page: int,
        page_size: int,
    ) -> PaginationResponse[VkGroupUser]:
        query = (
            select(VkGroupUserDb)
            .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
            .where(VkGroupDb.parser_request_id == parser_request_id)
        )
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=VkGroupUser,
        )

    async def admin_pagination_users_advanced_filter(
        self,
        parser_request_id: int,
        filtered_city: str,
        filtered_year_from: str,
        filtered_year_to: str,
        filtered_sex: str,
        page: int,
        page_size: int,
    ) -> PaginationResponse[VkGroupUser]:
        query = (
            select(VkGroupUserDb)
            .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
            .where(VkGroupDb.parser_request_id == parser_request_id)
        )

        if filtered_city is not None:
            if filtered_city == "None":
                query = query.filter(VkGroupUserDb.city.is_(None))
            elif filtered_city != "all_cities":
                query = query.filter(VkGroupUserDb.city == filtered_city)
        if filtered_year_from is not None:
            from_date = dt.datetime.strptime(f"01.01.{filtered_year_from}", "%d.%m.%Y")
            query = query.filter(VkGroupUserDb.birth_date >= from_date)
        if filtered_year_to is not None:
            to_date = dt.datetime.strptime(f"01.01.{filtered_year_to}", "%d.%m.%Y")
            query = query.filter(VkGroupUserDb.birth_date <= to_date)
        if filtered_sex is not None and filtered_sex != "all_sex":
            query = query.filter(VkGroupUserDb.sex == filtered_sex)

        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=VkGroupUser,
        )

    async def admin_pagination_users_filtered(
        self,
        parser_request_id: int,
        filtered_city: str | None,
        filtered_year_from: str,
        filtered_year_to: str,
        page: int,
        page_size: int,
    ) -> PaginationResponse[VkGroupUser]:
        if filtered_city and filtered_year_from and filtered_year_to:
            if filtered_city == "None":
                filtered_city = None
            if filtered_city != "all_cities":
                query = (
                    select(VkGroupUserDb)
                    .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
                    .filter(
                        (VkGroupDb.parser_request_id == parser_request_id)
                        & (VkGroupUserDb.city == filtered_city)
                        & (VkGroupUserDb.birth_date >= dt.datetime.strptime(f"01.01.{filtered_year_from}", "%d.%m.%Y"))
                        & (VkGroupUserDb.birth_date <= dt.datetime.strptime(f"01.01.{filtered_year_to}", "%d.%m.%Y"))
                    )
                )
            else:
                query = (
                    select(VkGroupUserDb)
                    .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
                    .filter(
                        (VkGroupDb.parser_request_id == parser_request_id)
                        & (VkGroupUserDb.birth_date >= dt.datetime.strptime(f"01.01.{filtered_year_from}", "%d.%m.%Y"))
                        & (VkGroupUserDb.birth_date <= dt.datetime.strptime(f"01.01.{filtered_year_to}", "%d.%m.%Y"))
                    )
                )
        else:
            query = (
                select(VkGroupUserDb)
                .join(VkGroupDb, VkGroupUserDb.vk_group_id == VkGroupDb.id)
                .filter(
                    (VkGroupDb.parser_request_id == parser_request_id)
                    & (VkGroupUserDb.birth_date >= dt.datetime.strptime(f"01.01.{filtered_year_from}", "%d.%m.%Y"))
                    & (VkGroupUserDb.birth_date <= dt.datetime.strptime(f"01.01.{filtered_year_to}", "%d.%m.%Y"))
                )
            )
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=VkGroupUser,
        )

    async def admin_pagination_messages(
        self,
        page: int,
        page_size: int,
        user_id: int,
    ) -> PaginationResponse[Messages]:
        query = select(MessagesDb).where(MessagesDb.user_id == user_id).order_by(MessagesDb.created_at.desc())
        return await self._paginate(
            query=query,
            page=page,
            page_size=page_size,
            model_type=Messages,
        )

    @inject_session
    async def get_detail(
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
        user_id: str,
    ) -> DetailParserRequest | None:
        query = (
            insert(ParserRequestDb)
            .values(
                input_data=input_data,
                user_id=user_id,
            )
            .returning(ParserRequestDb)
        )
        try:
            result: ScalarResult[ParserRequestDb] = await session.scalars(query)
            await session.commit()
        except DBAPIError:
            log.warning("Error in creating parser request: %s", input_data, exc_info=True)
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
            update(ParserRequestDb).where(ParserRequestDb.id == id_).values(status=status).returning(ParserRequestDb)
        )
        try:
            result = await session.scalars(query)
            await session.commit()
            return DetailParserRequest.model_validate(result.one())
        except DBAPIError as e:
            log.warning("Error updating: %s", e)

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
        result: Result,
        finished_at: datetime,
    ) -> None:
        query = (
            update(ParserRequestDb)
            .where(ParserRequestDb.id == id_)
            .values(
                finished_at=finished_at,
                status=RequestStatus.SUCCESSFUL,
                result_data=result.model_dump(),
            )
        )
        try:
            await session.execute(query)
            await session.commit()
        except DBAPIError:
            log.warning("Error save error")

    @inject_session
    async def stat_by_type(
        self, session: AsyncSession, parser_type: ParserTypes
    ) -> tuple[ParserTypes, Sequence[tuple[RequestStatus, int]]]:
        query = (
            select(ParserRequestDb.status, func.count())
            .group_by(
                ParserRequestDb.status,
            )
            .filter(ParserRequestDb.input_data["parser_type"].astext == parser_type)
        )
        return parser_type, (await session.execute(query)).fetchall()  # type: ignore[return-value]

    async def stat(self) -> Sequence[tuple[ParserTypes, RequestStatus, int]]:
        tasks = [self.stat_by_type(parser_type=pt) for pt in ParserTypes]
        stat = await gather(*tasks)
        output = []
        for pt, res in stat:
            for req_status, count in res:
                output.append((pt, req_status, count))
        return output

    @inject_session
    async def get_all_account_by_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Sequence[SendAccountsDb]:
        query = select(SendAccountsDb).where(
            SendAccountsDb.user_id == user_id,
        )
        result = await session.execute(query)
        return result.scalars().all()

    @inject_session
    async def get_random_account(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Sequence[SendAccountsDb]:
        query = select(SendAccountsDb).where(
            SendAccountsDb.user_id == user_id,
            SendAccountsDb.status == SendAccountStatus.ACTIVE,
        )
        result = await session.execute(query)
        return result.scalars().all()

    @inject_session
    async def get_random_message(
        self,
        session: AsyncSession,
        user_id: int,
        order: int,
    ) -> Sequence[MessagesDb]:
        query = select(MessagesDb).where(
            MessagesDb.user_id == user_id,
            MessagesDb.order == order,
        )
        result = await session.execute(query)
        return result.scalars().all()

    async def redirector(
        self,
        url: str,
    ) -> Exception:
        raise web.HTTPFound(url)

    @inject_session
    async def create_send_message(
        self,
        session: AsyncSession,
        user_id: int,
        parser_request_id: int,
        task_name: str,
        necessary_messages: int,
    ) -> SendMessages | None:
        query = (
            insert(SendMessagesDb)
            .values(
                user_id=user_id,
                parser_request_id=parser_request_id,
                task_name=task_name,
                successful_messages=0,
                necessary_messages=necessary_messages,
            )
            .returning(SendMessagesDb)
        )
        try:
            result: ScalarResult[SendMessagesDb] = await session.scalars(query)
            await session.commit()
        except DBAPIError:
            log.warning(
                "Error in creating send message: %s",
                task_name,
                exc_info=True,
            )
            return None
        return SendMessages.model_validate(result.one())

    @inject_session
    async def update_send_successful_messages(
        self,
        session: AsyncSession,
        user_id: int,
        task_name: str,
    ) -> SendMessages | None:
        query = (
            update(SendMessagesDb)
            .where(
                SendMessagesDb.user_id == user_id,
                SendMessagesDb.task_name == task_name,
                SendMessagesDb.status == SendMessageStatus.PROCESSING,
            )
            .values(
                successful_messages=SendMessagesDb.successful_messages + 1,
            )
            .returning(SendMessagesDb)
        )
        try:
            result = await session.scalars(query)
            await session.commit()
            return SendMessages.model_validate(result.one())
        except DBAPIError as e:
            log.warning("Error updating send message: %s", e)

        return None

    @inject_session
    async def save_send_message_successful_result(
        self,
        session: AsyncSession,
        id_: int,
    ) -> SendMessages | None:
        query = (
            update(SendMessagesDb)
            .where(SendMessagesDb.id == id_)
            .values(
                status=SendMessageStatus.SUCCESSFUL,
                finished_at=datetime.now(),
            )
            .returning(SendMessagesDb)
        )
        try:
            result = await session.scalars(query)
            await session.commit()
            return SendMessages.model_validate(result.one())
        except DBAPIError as e:
            log.warning("Error updating send message: %s", e)

        return None

    @inject_session
    async def save_send_message_error_result(
        self,
        session: AsyncSession,
        id_: int,
        error_message: str,
    ) -> SendMessages | None:
        query = (
            update(SendMessagesDb)
            .where(SendMessagesDb.id == id_)
            .values(
                status=SendMessageStatus.FAILED,
                finished_at=datetime.now(),
                error_message=error_message,
            )
            .returning(SendMessagesDb)
        )
        try:
            result = await session.scalars(query)
            await session.commit()
            return SendMessages.model_validate(result.one())
        except DBAPIError as e:
            log.warning("Error updating send message: %s", e)

        return None

    @inject_session
    async def create_vk_dialog(
        self,
        session: AsyncSession,
        send_account_id: int,
        vk_group_user_id: int,
    ) -> VkDialogs | None:
        query = (
            insert(VkDialogsDb)
            .values(
                send_account_id=int(send_account_id),
                vk_group_user_id=int(vk_group_user_id),
            )
            .returning(VkDialogsDb)
        )
        obj = (await session.scalars(query)).one()
        await session.commit()
        return VkDialogs.model_validate(obj)

    @inject_session
    async def create_vk_message(
        self,
        session: AsyncSession,
        dialog_id: int,
        message_id: int,
    ) -> VkMessages | None:
        query = (
            insert(VkMessagesDb)
            .values(
                dialog_id=dialog_id,
                message_id=message_id,
            )
            .returning(VkMessagesDb)
        )
        try:
            result: ScalarResult[VkMessagesDb] = await session.scalars(query)
            await session.commit()
        except DBAPIError:
            log.warning(
                "Error in creating vk messages: %s",
                dialog_id,
                exc_info=True,
            )
            return None
        return VkMessages.model_validate(result.one())
