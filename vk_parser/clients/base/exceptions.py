from typing import Any

from aiohttp import ClientError
from yarl import URL


class UnhandledStatus(ClientError, KeyError):
    status: int
    url: URL
    client_name: str | None

    def __init__(
        self,
        *args: Any,
        status: int,
        url: URL,
        client_name: str | None = None,
    ):
        super().__init__(*args)
        self.status = status
        self.url = url
        self.client_name = client_name
