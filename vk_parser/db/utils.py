import os
from argparse import Namespace
from collections.abc import Callable, Coroutine
from enum import StrEnum
from functools import wraps
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar

import orjson
import sqlalchemy.dialects.postgresql as pg
from alembic.config import Config
from sqlalchemy import Engine
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as sa_create_async_engine
from sqlalchemy.orm import sessionmaker

import vk_parser

PROJECT_PATH = Path(vk_parser.__file__).parent.parent.resolve()


R = TypeVar("R")
P = ParamSpec("P")


def inject_session(
    func: Callable[Concatenate[Any, AsyncSession, P], Coroutine[Any, Any, R]],
) -> Callable[Concatenate[Any, P], Coroutine[Any, Any, R]]:
    attr_name = "session_factory"

    @wraps(func)
    async def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        session_factory: async_sessionmaker[AsyncSession] = getattr(self, attr_name)

        async with session_factory() as session:
            return await func(self, session, *args, **kwargs)

    return wrapper


def create_async_engine(connection_uri: str, **engine_kwargs: Any) -> AsyncEngine:
    if engine_kwargs.get("json_serializer") is None:
        engine_kwargs["json_serializer"] = dumps
    if engine_kwargs.get("json_deserializer") is None:
        engine_kwargs["json_deserializer"] = orjson.loads
    return sa_create_async_engine(url=connection_uri, echo=True, **engine_kwargs)


def create_async_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def create_engine(connection_uri: str, **engine_kwargs: Any) -> Engine:
    if engine_kwargs.get("json_serializer") is None:
        engine_kwargs["json_serializer"] = orjson.dumps
    if engine_kwargs.get("json_deserializer") is None:
        engine_kwargs["json_deserializer"] = orjson.loads
    return sa_create_engine(url=connection_uri, **engine_kwargs)


def create_session_factory(
    engine: Engine,
) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def make_alembic_config(cmd_opts: Namespace, base_path: Path = PROJECT_PATH) -> Config:
    if not os.path.isabs(cmd_opts.config):
        cmd_opts.config = str(base_path / "vk_parser/db" / cmd_opts.config)

    config = Config(
        file_=cmd_opts.config,
        ini_section=cmd_opts.name,
        cmd_opts=cmd_opts,
    )

    alembic_location = config.get_main_option("script_location")
    if not alembic_location:
        raise ValueError
    if not os.path.isabs(alembic_location):
        config.set_main_option("script_location", str(base_path / alembic_location))

    if cmd_opts.pg_dsn:
        config.set_main_option("sqlalchemy.url", cmd_opts.pg_dsn)

    config.attributes["configure_logger"] = False

    return config


def dumps(*args: Any, **kwargs: Any) -> str:
    return orjson.dumps(*args, **kwargs).decode()


def _choices(enum_cls: type[StrEnum]) -> tuple[str, ...]:
    return tuple(map(str, enum_cls))


def make_pg_enum(enum_cls: type[StrEnum], **kwargs: Any) -> pg.ENUM:
    return pg.ENUM(
        enum_cls,
        values_callable=_choices,
        **kwargs,
    )
