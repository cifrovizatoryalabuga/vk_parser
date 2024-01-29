import logging

from aio_pika import Channel
from aio_pika.patterns import Master
from aiomisc import Service

from vk_parser.generals.enums import ParserTypes
from vk_parser.generals.models.amqp import AmqpVkInputData
from vk_parser.parsers.vk.parser import VkParser

log = logging.getLogger(__name__)


class VKParserService(Service):
    __required__ = ("parsing_queue_name",)
    __dependencies__ = (
        "amqp_parsing_channel",
        "vk_parser",
    )

    parsing_queue_name: str

    amqp_parsing_channel: Channel
    vk_parser: VkParser

    async def start(self) -> None:
        log.info(
            "About to start VkParserService to process queue %s",
            self.parsing_queue_name,
        )
        master = Master(self.amqp_parsing_channel)
        await master.create_worker(
            ParserTypes.VK_SIMPLE_PARSED_POSTS,
            self._process,
            durable=True,
        )
        log.info("VkParserService started")

    async def _process(
        self,
        msg: AmqpVkInputData,
    ) -> None:
        await self.vk_parser.process_request(input_data=msg)
