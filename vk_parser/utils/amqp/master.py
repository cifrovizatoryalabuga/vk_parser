import logging
from collections.abc import Awaitable, Mapping
from enum import StrEnum, unique
from typing import Any, TypeVar

import aiormq
from aio_pika import Message
from aio_pika.abc import (
    AbstractConnection,
    AbstractExchange,
    AbstractTransaction,
    DateType,
    TimeoutType,
)
from aio_pika.patterns import Master as BaseMaster
from pamqp.common import FieldValue
from pydantic import BaseModel

from vk_parser.generals.enums import ParserTypes
from vk_parser.utils.amqp import msgpack_serializer

log = logging.getLogger(__name__)

MasterType = TypeVar("MasterType", bound="Master")

PUB_SUB = "PUB.SUB"


@unique
class MessageHdrs(StrEnum):
    EVENT_TYPE = "Event-Type"
    PARSER_TYPE = "Parser-Type"
    FROM = "From"


class Master(BaseMaster):
    def __init__(self, exchange: AbstractExchange | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._exchange: AbstractExchange = exchange or self.channel.default_exchange

    @classmethod
    async def create_master(
        cls: type[MasterType],
        amqp: AbstractConnection,
        publisher_confirms: bool = True,
        prefetch_count: int = 100,
        on_return_raises: bool = True,
    ) -> MasterType:
        ch = await amqp.channel(
            publisher_confirms=publisher_confirms,
            on_return_raises=on_return_raises,
        )
        await ch.set_qos(prefetch_count=prefetch_count)

        log.debug("Declaration %s exchange", PUB_SUB)
        exchange = await ch.declare_exchange(
            PUB_SUB, auto_delete=False, durable=True, passive=False
        )

        return cls(channel=ch, exchange=exchange)

    def transaction(self) -> AbstractTransaction:
        return self.channel.transaction()

    @property
    def exchnage(self) -> AbstractExchange:
        return self._exchange

    def create_parser_event(
        self,
        parser_request: BaseModel,
        headers: Mapping[str, FieldValue] | None = None,
        timeout: TimeoutType = None,
        parser_type: ParserTypes = ParserTypes.VK_SIMPLE_PARSED_POSTS,
        expiration: DateType = None,
    ) -> Awaitable[aiormq.abc.ConfirmationFrameType | None]:
        if headers is None:
            headers = {}
        message = Message(
            body=self.serialize(parser_request),
            content_type=self.CONTENT_TYPE,
            delivery_mode=self.DELIVERY_MODE,
            expiration=expiration,
            headers={
                MessageHdrs.PARSER_TYPE: parser_type,
                MessageHdrs.FROM: "rest",
                **headers,
            },
        )

        return self.exchange.publish(
            message=message,
            routing_key=parser_type,
            timeout=timeout,
            mandatory=False,
        )


class MsgPackMaster(Master):
    CONTENT_TYPE = msgpack_serializer.CONTENT_TYPE
    SERIALIZER = msgpack_serializer
