import logging
from collections.abc import AsyncGenerator, AsyncIterator

import aio_pika
from aio_pika.abc import AbstractConnection
from aio_pika.patterns import Master
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from vk_parser.admin.arguments import parser
from vk_parser.clients.vk import VK_API_BASE_URL, Vk
from vk_parser.db.utils import create_async_engine, create_async_session_factory
from vk_parser.storages.authorization import AuthorizationStorage
from vk_parser.storages.parser_request import ParserRequestStorage
from vk_parser.storages.ping import PingStorage
from vk_parser.storages.vk import VkStorage
from vk_parser.utils.http import create_web_session

log = logging.getLogger(__name__)
args = parser.parse_args()


async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        connection_uri=str(args.pg_dsn),
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_async_session_factory(engine=engine)


def ping_storage(
    session_factory: async_sessionmaker[AsyncSession],
) -> PingStorage:
    return PingStorage(
        session_factory=session_factory,
    )


def vk_storage(
    session_factory: async_sessionmaker[AsyncSession],
) -> VkStorage:
    return VkStorage(session_factory=session_factory)


async def vk_client() -> AsyncGenerator[Vk, None]:
    async with create_web_session() as session:
        yield Vk(
            url=VK_API_BASE_URL,
            session=session,
            vk_api_service_token=args.vk_api_service_token,
            vk_api_version=args.vk_api_version,
        )


def auth_storage(
    session_factory: async_sessionmaker[AsyncSession],
) -> AuthorizationStorage:
    return AuthorizationStorage(session_factory=session_factory)


def parser_request_storage(
    session_factory: async_sessionmaker[AsyncSession],
) -> ParserRequestStorage:
    return ParserRequestStorage(
        session_factory=session_factory,
    )


async def amqp() -> AsyncIterator[AbstractConnection]:
    log.info("Starting AMQP robust connection")
    amqp_conn = await aio_pika.connect_robust(
        str(args.amqp_dsn),
        client_properties={
            "connection_name": "parser",
        },
    )
    async with amqp_conn:
        yield amqp_conn
    log.info("AMQP connection was closed")


async def amqp_master(amqp: AbstractConnection) -> AsyncIterator[Master]:
    async with amqp.channel() as channel:
        await channel.set_qos(
            prefetch_count=args.amqp_prefetch_count,
        )
        log.info(
            "Rmq channel for parsing created with prefetch count %d",
            args.amqp_prefetch_count,
        )
        yield Master(channel)
