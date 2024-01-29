from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import Any, NoReturn

import orjson
from aiohttp import ClientResponse


def value(value: Any) -> Callable:
    async def _getter(_: ClientResponse) -> Any:
        return value

    return _getter


def exception(error_type: type, *args: Any, **kwargs: Any) -> Callable:
    async def _raiser(_: ClientResponse) -> NoReturn:
        raise error_type(*args, **kwargs)

    return _raiser


def json_parser(parser: Callable, loads: Callable = orjson.loads) -> Callable:
    async def _parse(resp: ClientResponse) -> Any:
        resp_data = await resp.json(loads=loads)
        if iscoroutinefunction(parser):
            return await parser(resp_data)
        else:
            return parser(resp_data)

    return _parse


def text_parser(parser: Callable) -> Callable:
    async def _parse(resp: ClientResponse) -> Any:
        resp_data = await resp.text()
        if iscoroutinefunction(parser):
            return await parser(resp_data)
        else:
            return parser(resp_data)

    return _parse
