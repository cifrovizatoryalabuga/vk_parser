import inspect
from collections.abc import Callable, Mapping
from http import HTTPStatus
from typing import Any

from aiohttp import ClientResponse

from vk_parser.clients.base.exceptions import UnhandledStatus

ResponseHandlersType = Mapping[HTTPStatus | int | str, Callable]


async def apply_handler(
    handlers: ResponseHandlersType,
    resp: ClientResponse,
    client_name: str | None = None,
) -> Any:
    handler = _find_handler(handlers, resp.status)
    if not handler:
        raise UnhandledStatus(
            f"Unexpected response {resp.status} from {resp.url}",
            status=resp.status,
            url=resp.url,
            client_name=client_name,
        )
    res = handler(resp)
    if inspect.isawaitable(res):
        res = await res
    return res


def _find_handler(
    handlers: ResponseHandlersType,
    status: int,
) -> Callable | None:
    if status in handlers:
        return handlers[status]

    status_group = f"{int(status / 100)}xx"
    if status_group in handlers:
        return handlers[status_group]

    if "*" in handlers:
        return handlers["*"]

    return None
