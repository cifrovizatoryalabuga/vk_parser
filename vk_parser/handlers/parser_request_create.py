from aiohttp.web import Response, View
from aiohttp.web_exceptions import HTTPInternalServerError
from aiomisc import timeout

from vk_parser.generals.enums import ParserTypes, RequestStatus
from vk_parser.generals.models.amqp import AmqpVkInputData
from vk_parser.generals.models.parser_request import VkInputData
from vk_parser.handlers.base import CreateMixin, DependenciesMixin
from vk_parser.utils.http import fast_json_response


class ParserRequestCreateHandler(View, DependenciesMixin, CreateMixin):
    @timeout(5)
    async def post(self) -> Response:
        input_data = await self._parse_json(schema_type=VkInputData)

        parser_request = await self.parser_request_storage.create(
            input_data=input_data.model_dump(mode="json"),
        )
        if parser_request is None:
            raise HTTPInternalServerError(reason="Can't create parser request")
        await self.amqp_master.create_task(
            ParserTypes.VK_SIMPLE_PARSED_POSTS,
            kwargs=dict(
                msg=AmqpVkInputData(
                    parser_request_id=parser_request.id,
                    **input_data.model_dump(),
                )
            ),
        )
        parser_request = (
            await self.parser_request_storage.update_status(
                id_=parser_request.id,
                status=RequestStatus.QUEUED,
            )
            or parser_request
        )
        return fast_json_response(data=parser_request.model_dump(mode="json"))
