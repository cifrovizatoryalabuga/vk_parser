import logging

from aio_pika.patterns import Master
from aiomisc import Service

from vk_parser.generals.enums import ParserTypes
from vk_parser.parsers.vk import PostVkParser, SimpleVkParser

log = logging.getLogger(__name__)


class VKParserService(Service):
    __required__ = ("parsing_queue_name",)
    __dependencies__ = (
        "parser_request_storage",
        "post_vk_parser",
        "simple_vk_parser",
        "amqp_master",
    )

    parsing_queue_name: ParserTypes

    amqp_master: Master
    post_vk_parser: PostVkParser
    simple_vk_parser: SimpleVkParser

    async def start(self) -> None:
        log.info(
            "About to start VkParserService to process queue %s",
            self.parsing_queue_name,
        )

        if self.parsing_queue_name == ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS:
            await self.amqp_master.create_worker(
                ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS,
                self.post_vk_parser.process,
                durable=True,
            )
        elif self.parsing_queue_name == ParserTypes.VK_SIMPLE_DOWNLOAD:
            await self.amqp_master.create_worker(
                ParserTypes.VK_SIMPLE_DOWNLOAD,
                self.simple_vk_parser.process,
                durable=True,
            )
        log.info("VkParserService started with %s queue", self.parsing_queue_name)
