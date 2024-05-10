import asyncio
import os
import uuid
from collections.abc import Sequence
from random import choice

from vk_parser.db.models.vk_group_user import VkGroupUser as VkGroupUserDb
from vk_parser.db.models.vk_user_messanger import Messages as MessagesDb
from vk_parser.db.models.vk_user_messanger import SendAccounts as SendAccountsDb
from vk_parser.db.utils import create_async_engine, create_async_session_factory
from vk_parser.services.async_operations import (
    parser_request_storage,
    vk_client,
    vk_storage,
)

engine = create_async_engine(
    connection_uri=os.environ.get("APP_PG_DSN"),
    pool_pre_ping=True,
)

session_factory = create_async_session_factory(
    engine=engine,
)


class MessageSender:
    def __init__(
        self,
    ) -> None:
        self.parser_request_storage = parser_request_storage(session_factory)
        self.vk_client_generator = vk_client()
        self.vk_storage = vk_storage(session_factory)

    async def start_send_messages_task(
        self,
        user_id: int,
        parser_request_id: int,
        users: Sequence[VkGroupUserDb],
    ) -> asyncio.Task:
        task_name = str(uuid.uuid4())

        send_message = await self.parser_request_storage.create_send_message(
            user_id=user_id,
            parser_request_id=parser_request_id,
            task_name=task_name,
            necessary_messages=len(users),
        )

        try:
            send_messages_task = await asyncio.create_task(
                self.send_messages(user_id=user_id, users=users, task_name=task_name),
                name=task_name,
            )
            await self.parser_request_storage.save_send_message_successful_result(
                id_=send_message.id,
            )
        except Exception as e:
            await self.parser_request_storage.save_send_message_error_result(
                id_=send_message.id,
                error_message=str(e),
            )

        return send_messages_task

    async def send_messages(
        self,
        user_id: int,
        users: Sequence[VkGroupUserDb],
        task_name: str,
    ) -> None:
        for user in users:
            random_account = choice(await self.parser_request_storage.get_random_account(user_id=user_id))
            random_message = choice(
                await self.parser_request_storage.get_random_message(
                    user_id=user_id,
                    order=1,
                ),
            )
            await self.send_message_to_user(
                vk_group_user=user,
                account=random_account,
                message=random_message,
                user_id=user_id,
                is_update_successful=True,
                task_name=task_name,
            )
            await asyncio.sleep(10)

        return None

    async def send_message_to_user(
        self,
        vk_group_user: VkGroupUserDb,
        account: SendAccountsDb,
        message: MessagesDb,
        user_id: int,
        is_update_successful: bool = False,
        vk_dialog_id: int = None,
        task_name: str = None,
    ) -> None:
        async for vk in self.vk_client_generator:
            await vk.post_messages_send(
                user_id=vk_group_user.vk_user_id,
                message=message.message,
                access_token=account.secret_token,
                proxy=account.proxy,
            )

        if is_update_successful:
            await self.vk_storage.update_successful_messages_by_id(
                account_id=account.id,
            )
            if task_name:
                await self.parser_request_storage.update_send_successful_messages(
                    user_id=user_id,
                    task_name=task_name,
                )
        if vk_dialog_id is None:
            vk_dialog = await self.parser_request_storage.create_vk_dialog(
                send_account_id=account.id,
                vk_group_user_id=vk_group_user.id,
            )
            vk_dialog_id = vk_dialog.id

        await self.parser_request_storage.create_vk_message(
            dialog_id=vk_dialog_id,
            message_id=message.id,
        )

        return None
