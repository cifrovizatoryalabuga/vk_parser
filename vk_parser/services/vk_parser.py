import logging
from datetime import datetime

from aio_pika import Channel
from aio_pika.patterns import Master
from aiomisc import Service

from vk_parser.generals.enums import ParserTypes
from vk_parser.generals.models.amqp import AmqpVkInputData
from vk_parser.parsers.vk.parsers import PostVkParser, SimpleVkParser
from vk_parser.storages.parser_request import ParserRequestStorage

log = logging.getLogger(__name__)


class VKParserService(Service):
    __required__ = ("parsing_queue_name",)
    __dependencies__ = (
        "amqp_parsing_channel",
        "parser_request_storage",
        "post_vk_parser",
        "simple_vk_parser",
    )

    parsing_queue_name: ParserTypes

    amqp_parsing_channel: Channel
    parser_request_storage: ParserRequestStorage
    post_vk_parser: PostVkParser
    simple_vk_parser: SimpleVkParser

    async def start(self) -> None:
        log.info(
            "About to start VkParserService to process queue %s",
            self.parsing_queue_name,
        )
        master = Master(self.amqp_parsing_channel)
        if self.parsing_queue_name == ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS:
            await master.create_worker(
                ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS,
                self._process_vk_download_and_parsed_posts,
                durable=True,
            )
        elif self.parsing_queue_name == ParserTypes.VK_SIMPLE_DOWNLOAD:
            await master.create_worker(
                ParserTypes.VK_SIMPLE_DOWNLOAD,
                self._process_vk_simple_download,
                durable=True,
            )
        log.info("VkParserService started with %s queue", self.parsing_queue_name)

    async def _process_vk_download_and_parsed_posts(
        self,
        *,
        input_data: AmqpVkInputData,
    ) -> None:
        try:
            await self.post_vk_parser.process_request(input_data=input_data)
        except Exception as e:
            log.exception("process vk download and parsed posts")
            await self.parser_request_storage.save_error(
                id_=input_data.parser_request_id,
                finished_at=datetime.now(),
                error_message=str(e),
            )

    async def _process_vk_simple_download(
        self,
        *,
        input_data: AmqpVkInputData,
    ) -> None:
        try:
            await self.simple_vk_parser.process_request(input_data=input_data)
        except Exception as e:
            log.exception("process vk simple download")
            await self.parser_request_storage.save_error(
                id_=input_data.parser_request_id,
                finished_at=datetime.now(),
                error_message=str(e),
            )
