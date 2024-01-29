from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vk_parser.db.utils import inject_session


@dataclass(frozen=True, slots=True)
class PingStorage:
    session_factory: async_sessionmaker[AsyncSession]

    @inject_session
    async def ping(self, session: AsyncSession) -> bool:
        try:
            await session.execute(text("select 1"))
        except SQLAlchemyError:
            return False
        return True
