from collections.abc import Mapping
from typing import Any, TypeVar

import msgpack
from aio_pika.abc import AbstractIncomingMessage
from pydantic import BaseModel, ValidationError

from vk_parser.utils.amqp import msgpack_serializer
from vk_parser.utils.amqp.exceptions import UnpackException

MessageModel = TypeVar("MessageModel", bound=BaseModel)


def _unpack_message_body(message: AbstractIncomingMessage) -> Mapping[Any, Any]:
    try:
        message_body = msgpack_serializer.loads(message.body)
    except (msgpack.UnpackException, ValueError) as error:
        raise UnpackException("Message body not able be unpacked") from error
    if not isinstance(message_body, Mapping):
        raise UnpackException("Message body should be a dictionary")
    return message_body


def parse_incoming_message(
    message: AbstractIncomingMessage,
    model: type[MessageModel],
) -> MessageModel:
    try:
        return model.model_validate(_unpack_message_body(message))
    except (ValueError, TypeError, ValidationError) as error:
        raise UnpackException("Incorrect data") from error
