from typing import Any

from aiohttp import ClientSession
from aiohttp.client import DEFAULT_TIMEOUT
from yarl import URL

from vk_parser.clients.base.root_handler import ResponseHandlersType, apply_handler
from vk_parser.clients.base.timeout import TimeoutType, get_timeout


class BaseHttpClient:
    __slots__ = ("_url", "_session", "_client_name")

    _url: URL
    _session: ClientSession
    _client_name: str | None

    def __init__(
        self,
        url: URL,
        session: ClientSession,
        client_name: str | None = None,
    ):
        self._url = url
        self._session = session
        self._client_name = client_name

    @property
    def url(self) -> URL:
        return self._url

    async def _make_req(
        self,
        method: str,
        url: URL,
        handlers: ResponseHandlersType,
        timeout: TimeoutType = DEFAULT_TIMEOUT,
        **kwargs: Any,
    ) -> Any:
        async with self._session.request(
            method=method,
            url=url,
            timeout=get_timeout(timeout),
            **kwargs,
        ) as resp:
            return await apply_handler(
                handlers=handlers,
                resp=resp,
                client_name=self._client_name,
            )
