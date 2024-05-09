import os
import time
from datetime import datetime, timedelta
from random import choice

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from vk_parser.admin.message_sender import MessageSender
from vk_parser.clients.vk import VK_API_BASE_URL, Vk
from vk_parser.db.models.send_message import SendMessages as SendMessagesDb
from vk_parser.db.models.vk_group_user import VkGroupUser as VkGroupUserDb
from vk_parser.db.models.vk_messages import VkDialogs as VkDialogsDb
from vk_parser.db.models.vk_messages import VkMessages as VkMessagesDb
from vk_parser.db.models.vk_user_messanger import Messages as MessagesDb
from vk_parser.db.models.vk_user_messanger import SendAccounts as SendAccountsDb
from vk_parser.db.utils import create_async_engine, create_async_session_factory
from vk_parser.generals.enums import SendAccountStatus, VkDialogsStatus
from vk_parser.utils.http import create_web_session

engine = create_async_engine(
    connection_uri=os.environ.get("APP_PG_DSN"),
    pool_pre_ping=True,
)

session_factory = create_async_session_factory(
    engine=engine,
)


class Tasks():
    async def delete_archive_accounts(self):
        async with AsyncSession(engine) as session:
            async with session.begin():
                await session.execute(
                    delete(SendAccountsDb)
                    .where(SendAccountsDb.status == SendAccountStatus.ARCHIVE)
                )

    async def delete_old_send_messages(self):
        async with AsyncSession(engine) as session:
            async with session.begin():
                one_week_ago = datetime.now() - timedelta(weeks=1)
                await session.execute(
                    delete(SendMessagesDb)
                    .where(SendMessagesDb.created_at < one_week_ago)
                )

    async def reset_send_accounts(self):
        async with AsyncSession(engine) as session:
            async with session.begin():
                await session.execute(
                    update(SendAccountsDb)
                    .values(
                        status=SendAccountStatus.ACTIVE,
                        successful_messages=0,
                    )
                )

    async def dialogue(self):
        async with AsyncSession(engine) as session:
            async with session.begin():
                vk_dialogs_result = await session.execute(
                    select(VkDialogsDb, SendAccountsDb, VkGroupUserDb)
                    .join(SendAccountsDb, VkDialogsDb.send_account_id == SendAccountsDb.id)
                    .join(VkGroupUserDb, VkDialogsDb.vk_group_user_id == VkGroupUserDb.id)
                    .where(VkDialogsDb.status == VkDialogsStatus.PROCESSING)
                )

                vk_dialogs = vk_dialogs_result.fetchall()

                for vk_dialog, send_account, vk_group_user in vk_dialogs:
                    async with create_web_session() as web_session:
                        vk_client = Vk(
                            url=VK_API_BASE_URL,
                            session=web_session,
                            vk_api_service_token=send_account.secret_token,
                            vk_api_version="5.81",
                        )

                        conversations = await vk_client.get_conversations_by_id(
                            access_token=send_account.secret_token,
                            proxy=send_account.proxy,
                            peer_ids=str(vk_group_user.vk_user_id),
                        )
                        for conversation in conversations.items:
                            conversation_messages = await vk_client.get_by_conversation_message_id(
                                access_token=send_account.secret_token,
                                proxy=send_account.proxy,
                                peer_id=conversation.peer.id,
                                conversation_message_ids=conversation.last_conversation_message_id,
                            )
                            for conversation_message in conversation_messages.items:
                                query = (
                                    select(func.max(MessagesDb.order))
                                    .join(VkMessagesDb, MessagesDb.id == VkMessagesDb.message_id)
                                    .join(VkDialogsDb, VkMessagesDb.dialog_id == VkDialogsDb.id)
                                    .where(VkDialogsDb.id == vk_dialog.id)
                                )

                                result = await session.execute(query)
                                max_order = result.scalar()

                                query = select(MessagesDb).where(
                                    MessagesDb.user_id == send_account.user_id,
                                    MessagesDb.order == max_order + 1,
                                )
                                vk_messages = await session.execute(query)
                                vk_messages_list = vk_messages.scalars().all()

                                if vk_messages_list:
                                    vk_message = choice(vk_messages_list)

                                    if vk_group_user.vk_user_id == conversation_message.from_id:
                                        message_sender = MessageSender()
                                        await message_sender.send_message_to_user(
                                            vk_group_user=vk_group_user,
                                            account=send_account,
                                            message=vk_message,
                                            user_id=send_account.user_id,
                                            vk_dialog_id=vk_dialog.id,
                                        )
                                    else:
                                        current_unix_time = int(time.time())
                                        time_difference_seconds = current_unix_time - conversation_message.date
                                        week_unix_time = 604800

                                        if time_difference_seconds >= week_unix_time:
                                            await session.execute(
                                                update(VkDialogsDb)
                                                .where(VkDialogsDb.id == vk_dialog.id)
                                                .values(
                                                    status=VkDialogsStatus.SUCCESSFUL,
                                                )
                                            )
                                else:
                                    await session.execute(
                                        update(VkDialogsDb)
                                        .where(VkDialogsDb.id == vk_dialog.id)
                                        .values(
                                            status=VkDialogsStatus.SUCCESSFUL,
                                        )
                                    )
