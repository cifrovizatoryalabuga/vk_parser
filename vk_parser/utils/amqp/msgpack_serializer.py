import struct
from datetime import datetime
from decimal import Decimal
from functools import singledispatch
from math import modf
from pathlib import Path
from typing import Any, NoReturn
from uuid import UUID

import msgpack
import pytz
from pydantic import BaseModel

CONTENT_TYPE = "application/msgpack"


def to_utc(timestamp: datetime) -> datetime:
    if not timestamp.tzname():
        return timestamp.replace(tzinfo=pytz.utc)
    elif timestamp.tzinfo != pytz.utc:
        return timestamp.astimezone(pytz.utc)
    return timestamp


@singledispatch
def pack(obj: Any) -> NoReturn:
    raise TypeError(f"Unknown type: {obj!r}")


@pack.register(UUID)
def _uuid_packer(obj: UUID) -> bytes:
    return obj.bytes


@pack.register(BaseModel)
def _model_packer(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True)


@pack.register(Path)
def _path_packer(obj: Path) -> str:
    return str(obj)


@pack.register(Decimal)
def _decimal_packer(obj: Decimal) -> str:
    return str(obj)


@pack.register(frozenset)
@pack.register(set)
def _frozenset_packer(obj: set) -> list[Any]:
    return list(obj)


# Note that go implementation of timestamp has incorrect order of s, ns,
# but should be ns, s according to msgpack specs.
@pack.register
def pack_datetime(obj: datetime) -> msgpack.ExtType:
    ns, s = modf(to_utc(obj).timestamp())
    return msgpack.ExtType(code=5, data=struct.pack(">qI", int(s), int(ns * 1e9)))


def unpack_datetime(data: bytes) -> datetime:
    s, ns = struct.unpack(">qI", data)
    ts = s + ns * 1e-9
    return datetime.fromtimestamp(ts, tz=pytz.utc)


def ext_hook(code: Any, data: Any) -> msgpack.ExtType:
    if code == 5:
        return unpack_datetime(data)
    return msgpack.ExtType(code, data)


def loads(data: bytes) -> Any:
    return msgpack.unpackb(data, raw=False, ext_hook=ext_hook)


def dumps(data: Any) -> bytes:
    return msgpack.packb(data, use_bin_type=True, default=pack)
