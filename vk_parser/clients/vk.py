import logging
from collections.abc import Callable, Sequence
from datetime import date, datetime
from enum import IntEnum, StrEnum, unique
from functools import wraps
from http import HTTPStatus
from types import MappingProxyType
from typing import Any, ClassVar

from aiohttp import ClientResponse, ClientSession, hdrs
from aiomisc import asyncretry, timeout
from pydantic import BaseModel, Field, ValidationError
from yarl import URL

from vk_parser.clients.base.client import BaseHttpClient
from vk_parser.clients.base.root_handler import ResponseHandlersType
from vk_parser.clients.base.timeout import TimeoutType
from vk_parser.generals.exceptions import VkParserTooManyRequestsException

log = logging.getLogger(__name__)

VK_API_BASE_URL = URL("https://api.vk.com")
ERROR_KEY = "error"


class VkGroupWallType(IntEnum):
    OFF = 0
    OPEN = 1
    LIMITED = 2
    CLOSED = 3


class VkGroup(BaseModel):
    id: int
    name: str
    screen_name: str
    members_count: int
    wall: VkGroupWallType


class VkGroups(BaseModel):
    groups: Sequence[VkGroup]


class VkLastSeen(BaseModel):
    platform: int | None = None
    time: datetime


class VkGroupMember(BaseModel):
    id: int
    birth_date: str | None = Field(alias="bdate", default=None)
    first_name: str | None = None
    last_name: str | None = None
    last_seen: VkLastSeen | None = None
    sex: int | None = Field(alias="sex", default=None)
    city: dict | None = Field(alias="city", default=None)
    university: dict | None = Field(alias="university", default=None)
    photo_100: str | None = Field(alias="photo_100", default="https://vk.com/images/camera_100.png")

    def in_age_range(self, max_age: int) -> bool:
        if not self.birth_date:
            return False
        try:
            birth_dt = datetime.strptime(self.birth_date, "%d.%m.%Y")
        except ValueError:
            return False
        today = datetime.now()
        age = today.year - birth_dt.year
        if (today.month, today.day) < (birth_dt.month, birth_dt.day):
            age -= 1
        return age <= max_age

    @property
    def parsed_birth_date(self) -> date | None:
        if self.birth_date is None:
            return None
        try:
            birth_dt = datetime.strptime(self.birth_date, "%d.%m.%Y")
        except ValueError:
            return None
        return birth_dt.date()

    @property
    def last_visit_vk_date(self) -> date | None:
        return self.last_seen.time.date() if self.last_seen else None


class VkGroupMembers(BaseModel):
    count: int
    items: list[VkGroupMember]


class VkWallPost(BaseModel):
    id: int
    owner_id: int
    text: str
    date: datetime
    user_vk_ids: Sequence[int] = Field(default_factory=list)

    @property
    def date_without_tz(self) -> datetime:
        return self.date.replace(tzinfo=None)

    @property
    def url(self) -> str:
        return f"https://vk.com/wall{self.owner_id}_{self.id}"


class VkWallPosts(BaseModel):
    count: int
    items: Sequence[VkWallPost]


@unique
class VkObjectType(StrEnum):
    USER = "user"
    GROUP = "group"
    EVENT = "event"
    PAGE = "page"
    APPLICATION = "application"
    VK_APP = "vk_app"


class VkResolvedObject(BaseModel):
    object_id: int
    type: VkObjectType


def parse_vk_response(func: Callable) -> Callable:
    @wraps(func)
    async def _parse(response: ClientResponse) -> Any:
        data = await response.json()
        if ERROR_KEY in data:
            log.warning("VK parser too many requests")
            raise VkParserTooManyRequestsException
        return await func(data=data)

    return _parse


@parse_vk_response
async def parse_wall_posts(data: dict[str, Any]) -> VkWallPosts | None:
    try:
        posts = VkWallPosts(**data["response"])
    except ValidationError:
        return None
    return posts


@parse_vk_response
async def parse_vk_group(data: dict[str, Any]) -> VkGroup | None:
    try:
        groups = VkGroups(**data["response"])
    except ValidationError:
        return None
    except KeyError:
        log.warning("Got key error with data %s", data)
        return None
    return groups.groups[0]


@parse_vk_response
async def parse_group_members(data: dict[str, Any]) -> VkGroupMembers | None:
    try:
        group_members = VkGroupMembers(**data["response"])
    except ValidationError:
        return None
    except KeyError:
        log.warning("Got key error with data %s", data)
        return None
    return group_members


@parse_vk_response
async def parse_resolve_screen_name(data: dict[str, Any]) -> VkResolvedObject | None:
    try:
        resolved_object = VkResolvedObject(**data["response"])
    except ValidationError:
        return None
    except KeyError:
        log.warning("Got key error with data %s", data)
        return None
    return resolved_object


async def parse_ping(resp: ClientResponse) -> bool:
    data = await resp.json()
    if "error" in data:
        return False
    return True


class Vk(BaseHttpClient):
    DEFAULT_TIMEOUT: ClassVar[TimeoutType] = 5

    GET_GROUP_BY_ID_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            HTTPStatus.OK: parse_vk_group,
        }
    )

    GET_GROUP_MEMBERS_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            HTTPStatus.OK: parse_group_members,
        }
    )

    GET_WALL_POSTS_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            HTTPStatus.OK: parse_wall_posts,
        }
    )

    GET_PING_HANDLERS: ResponseHandlersType = MappingProxyType(
        {
            HTTPStatus.OK: parse_ping,
        }
    )

    RESOLVE_SCREEN_NAME: ResponseHandlersType = MappingProxyType(
        {
            HTTPStatus.OK: parse_resolve_screen_name,
        }
    )

    DEFAULT_FIELDS_GROUPS_GET_BY_ID: ClassVar[Sequence[str]] = ("members_count", "wall")
    DEFAULT_FIELDS_GROUPS_GET_MEMBERS: ClassVar[Sequence[str]] = ("bdate", "last_seen", "sex", "city", "photo_100", "university")

    def __init__(
        self,
        url: URL,
        session: ClientSession,
        vk_api_service_token: str,
        vk_api_version: str,
        client_name: str | None = None,
    ):
        super().__init__(url, session, client_name)
        self._default_kwargs = {
            "access_token": vk_api_service_token,
            "v": vk_api_version,
        }

    @asyncretry(max_tries=8, pause=1)
    async def get_group_by_id(
        self,
        group_id: int,
        fields: Sequence[str] = DEFAULT_FIELDS_GROUPS_GET_BY_ID,
        timeout: TimeoutType = DEFAULT_TIMEOUT,
    ) -> VkGroup | None:
        log.info("Request VK API method: groups.getById %s", group_id)
        return await self._make_req(
            method=hdrs.METH_POST,
            url=self._url / "method/groups.getById",
            handlers=self.GET_GROUP_BY_ID_HANDLERS,
            timeout=timeout,
            data={
                "group_id": group_id,
                "fields": ",".join(fields),
                **self._default_kwargs,
            },
        )

    @asyncretry(max_tries=8, pause=1)
    async def get_group_members(
        self,
        group_id: int,
        fields: Sequence[str] = DEFAULT_FIELDS_GROUPS_GET_MEMBERS,
        offset: int = 0,
        count: int = 1000,
        timeout: TimeoutType = DEFAULT_TIMEOUT,
    ) -> VkGroupMembers | None:
        log.info(
            "Request VK API method: groups.getMembers %s %s %s",
            group_id,
            offset,
            count,
        )
        return await self._make_req(
            method=hdrs.METH_POST,
            url=self._url / "method/groups.getMembers",
            handlers=self.GET_GROUP_MEMBERS_HANDLERS,
            timeout=timeout,
            data={
                "group_id": group_id,
                "offset": offset,
                "fields": ",".join(fields),
                "count": count,
                **self._default_kwargs,
            },
        )

    @asyncretry(max_tries=12, pause=1)
    async def get_group_posts(
        self,
        group_id: int,
        offset: int,
        count: int = 100,
        timeout: TimeoutType = DEFAULT_TIMEOUT,
    ) -> VkWallPosts | None:
        log.info("Request VK API method: wall.get %s %s %s", group_id, offset, count)
        return await self._make_req(
            method=hdrs.METH_POST,
            url=self._url / "method/wall.get",
            handlers=self.GET_WALL_POSTS_HANDLERS,
            timeout=timeout,
            data={
                "owner_id": -group_id,
                "offset": offset,
                "count": count,
                **self._default_kwargs,
            },
        )

    @timeout(value=2)
    @asyncretry(max_tries=12, pause=1)
    async def ping(self, timeout: TimeoutType = DEFAULT_TIMEOUT) -> bool:
        log.info("Request VK API method: users.get")
        return await self._make_req(
            method=hdrs.METH_POST,
            url=self._url / "method/users.get",
            handlers=self.GET_PING_HANDLERS,
            timeout=timeout,
            data={
                "user_ids": 1,
                **self._default_kwargs,
            },
        )

    @asyncretry(max_tries=8, pause=1)
    async def resolve_screen_name(
        self,
        screen_name: str,
        timeout: TimeoutType = DEFAULT_TIMEOUT,
    ) -> VkResolvedObject | None:
        return await self._make_req(
            method=hdrs.METH_POST,
            url=self._url / "method/utils.resolveScreenName",
            handlers=self.RESOLVE_SCREEN_NAME,
            timeout=timeout,
            data={
                "screen_name": screen_name,
                **self._default_kwargs,
            },
        )

    @asyncretry(max_tries=8, pause=1)
    async def get_user_info(
        self,
        group_id: int,
        fields: Sequence[str] = DEFAULT_FIELDS_GROUPS_GET_MEMBERS,
        offset: int = 0,
        count: int = 1000,
        timeout: TimeoutType = DEFAULT_TIMEOUT,
    ) -> VkGroupMembers | None:
        log.info(
            "Request VK API method: groups.getMembers %s %s %s",
            group_id,
            offset,
            count,
        )
        return await self._make_req(
            method=hdrs.METH_POST,
            url=self._url / "method/groups.getMembers",
            handlers=self.GET_GROUP_MEMBERS_HANDLERS,
            timeout=timeout,
            data={
                "group_id": group_id,
                "offset": offset,
                "fields": ",".join(fields),
                "count": count,
                **self._default_kwargs,
            },
        )
