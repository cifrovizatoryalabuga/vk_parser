import os

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from vk_parser.db.models.vk_user_messanger import SendAccounts as SendAccountsDb
from vk_parser.db.utils import create_async_engine
from vk_parser.generals.enums import SendAccountStatus

engine = create_async_engine(
    connection_uri=os.environ.get("APP_PG_DSN"),
    pool_pre_ping=True,
)


async def delete_archive_accounts():
    async with AsyncSession(engine) as session:
        async with session.begin():
            await session.execute(
                delete(SendAccountsDb)
                .where(SendAccountsDb.status == SendAccountStatus.ARCHIVE)
            )
