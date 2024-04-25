import os
from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from vk_parser.db.models.send_message import SendMessages as SendMessagesDb
from vk_parser.db.utils import create_async_engine

engine = create_async_engine(
    connection_uri=os.environ.get("APP_PG_DSN"),
    pool_pre_ping=True,
)


async def delete_old_send_messages():
    async with AsyncSession(engine) as session:
        async with session.begin():
            one_week_ago = datetime.now() - timedelta(weeks=1)

            await session.execute(
                delete(SendMessagesDb)
                .where(SendMessagesDb.created_at < one_week_ago)
            )
