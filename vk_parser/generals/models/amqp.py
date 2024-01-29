from vk_parser.generals.models.parser_request import VkInputData


class AmqpVkInputData(VkInputData):
    parser_request_id: int
