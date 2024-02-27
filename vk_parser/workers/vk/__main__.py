import logging

from aiomisc import Service, entrypoint
from aiomisc_log import basic_config

from vk_parser.generals.enums import VK_PARSER_TYPES
from vk_parser.services.vk_parser import VKParserService
from vk_parser.workers.vk.arguments import parser
from vk_parser.workers.vk.deps import config_deps

log = logging.getLogger(__name__)


def main() -> None:
    args = parser.parse_args()
    basic_config(level=args.log_level, log_format=args.log_format)
    config_deps(args)

    if args.amqp_queue_name not in VK_PARSER_TYPES:
        raise ValueError("Incorrect amqp_queue_name")
    services: list[Service] = [
        VKParserService(parsing_queue_name=args.amqp_queue_name),
    ]

    with entrypoint(
        *services,
        log_level=args.log_level,
        log_format=args.log_format,
        pool_size=args.pool_size,
        debug=args.debug,
    ) as loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
