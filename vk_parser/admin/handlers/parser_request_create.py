from aiohttp.web import Response, View
from aiohttp.web_exceptions import HTTPInternalServerError
from aiomisc import timeout

from vk_parser.admin.handlers.base import CreateMixin, DependenciesMixin
from vk_parser.generals.enums import RequestStatus
from vk_parser.generals.models.parser_request import (
    ParsePostsVkInputData,
    SimpleVkInputData,
)
from vk_parser.utils.http import fast_json_response


class ParserRequestCreateHandler(View, DependenciesMixin, CreateMixin):
    @timeout(5)
    async def post(self) -> Response:
        input_data = await self._parse_json(
            schemas=[ParsePostsVkInputData, SimpleVkInputData],
        )

        parser_request = await self.parser_request_storage.create(
            input_data=input_data.model_dump(mode="json"),
        )
        if parser_request is None:
            raise HTTPInternalServerError(reason="Can't create parser request")
        parser_request = (
            await self.parser_request_storage.update_status(
                id_=parser_request.id,
                status=RequestStatus.QUEUED,
            )
            or parser_request
        )
        await self.amqp_master.create_task(
            input_data.parser_type,  # type: ignore[attr-defined]
            kwargs=dict(
                parser_request_id=parser_request.id,
                input_data=input_data.model_dump(),
            ),
        )
        return fast_json_response(data=parser_request.model_dump(mode="json"))
