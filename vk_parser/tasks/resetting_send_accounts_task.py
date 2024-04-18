import os

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from vk_parser.db.models.vk_user_messanger import SendAccounts as SendAccountsDb
from vk_parser.db.utils import create_async_engine

engine = create_async_engine(
    connection_uri=os.environ.get("APP_PG_DSN"),
    pool_pre_ping=True,
)


async def reset_send_accounts():
    async with AsyncSession(engine) as session:
        async with session.begin():
            await session.execute(
                update(SendAccountsDb).
                values(is_disabled=False, successful_messages=0)
            )
        await session.commit()
