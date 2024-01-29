from dataclasses import dataclass

from aio_pika import Message
from aio_pika.abc import AbstractExchange, AbstractIncomingMessage
from aio_pika.message import DateType


@dataclass(frozen=True)
class RetryMaster:
    exchange: AbstractExchange
    queue_name: str
    pause: DateType

    async def retry(self, message: AbstractIncomingMessage) -> None:
        retry_msg = Message(
            body=message.body,
            content_type=message.content_type,
            delivery_mode=message.delivery_mode,
            headers=message.headers,
            expiration=self.pause,
        )
        await self.exchange.publish(
            message=retry_msg,
            routing_key=self.queue_name,
        )
