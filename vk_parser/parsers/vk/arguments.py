import argparse

import configargparse
from aiomisc.log import LogFormat, LogLevel
from yarl import URL

from vk_parser.generals.enums import ParserTypes

parser = configargparse.ArgumentParser(
    allow_abbrev=False,
    auto_env_var_prefix="APP_",
    description="VK parser",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument("-D", "--debug", action="store_true")
parser.add_argument("-s", "--pool-size", type=int, default=4, help="Thread pool size")
parser.add_argument(
    "--forks",
    type=int,
    default=4,
    help="Number of process to download",
)

group = parser.add_argument_group("Logging options")
group.add_argument(
    "--log-level",
    default=LogLevel.info,
    choices=LogLevel.choices(),
)
group.add_argument(
    "--log-format",
    default=LogFormat.color,
    choices=LogFormat.choices(),
)

group = parser.add_argument_group("VK API tokens")
group.add_argument("--vk-api-secure-key", type=str, required=True)
group.add_argument("--vk-api-service-token", type=str, required=True)
group.add_argument("--vk-api-version", type=str, default="5.199")

group = parser.add_argument_group("PostgreSQL options")
group.add_argument("--pg-dsn", required=True, type=URL)

group = parser.add_argument_group("AMQP options")
group.add_argument("--amqp-dsn", required=True, type=URL)
group.add_argument("--amqp-prefetch-count", type=int, default=4)
group.add_argument("--amqp-retry-pause-seconds", type=int, default=60)
group.add_argument("--amqp-retry-count-limit", type=int, default=2)
group.add_argument(
    "--amqp-queue-name",
    type=ParserTypes,
    default=ParserTypes.VK_DOWNLOAD_AND_PARSED_POSTS,
)
