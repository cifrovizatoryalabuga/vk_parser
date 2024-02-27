import logging
from abc import ABC
from datetime import datetime
from typing import Any

from vk_parser.generals.enums import RequestStatus
from vk_parser.generals.models.parser_request import Result
from vk_parser.storages.parser_request import ParserRequestStorage

log = logging.getLogger(__name__)


class BaseParser(ABC):
    parser_request_storage: ParserRequestStorage

    async def process(self, parser_request_id: int, input_data: dict[str, Any]) -> None:
        await self.parser_request_storage.update_status(
            id_=parser_request_id,
            status=RequestStatus.PROCESSING,
        )
        try:
            log.info("Start process request: %d", parser_request_id)
            await self._process(
                parser_request_id=parser_request_id, input_data=input_data
            )
            log.info("Finished process request: %d", parser_request_id)
        except Exception as e:  # noqa: BLE001
            log.warning("Error processing with data: %s", input_data, exc_info=True)
            await self.parser_request_storage.save_error(
                id_=parser_request_id,
                finished_at=datetime.now(),
                error_message=str(e),
            )

    async def _process(
        self, parser_request_id: int, input_data: dict[str, Any]
    ) -> None:
        raise NotImplementedError

    async def _save_empty_result(self, parser_request_id: int, message: str) -> None:
        await self.parser_request_storage.save_empty_result(
            id_=parser_request_id,
            finished_at=datetime.now(),
            message=message,
        )

    async def _save_successful_result(
        self, parser_request_id: int, result: Result
    ) -> None:
        await self.parser_request_storage.save_successful_result(
            id_=parser_request_id, result=result, finished_at=datetime.now()
        )
