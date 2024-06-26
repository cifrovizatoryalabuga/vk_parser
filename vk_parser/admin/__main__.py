import logging

from aiomisc import Service, entrypoint
from aiomisc_log import basic_config

from vk_parser.admin.arguments import parser
from vk_parser.admin.deps import config_deps
from vk_parser.admin.service import Admin
from vk_parser.admin.tasks import Tasks
from vk_parser.utils.scheduler import SchedulerService

log = logging.getLogger(__name__)


def main() -> None:
    args = parser.parse_args()
    basic_config(level=args.log_level, log_format=args.log_format)
    config_deps(args)

    tasks = Tasks()

    scheduler_service = SchedulerService(
        jobs=[
            {
                "func": tasks.reset_send_accounts,
                "trigger": "cron",
                "hour": 3,
            },
            {
                "func": tasks.delete_archive_accounts,
                "trigger": "cron",
                "hour": 4,
            },
            {
                "func": tasks.delete_old_send_messages,
                "trigger": "cron",
                "hour": 5,
                "day_of_week": "sun",
            },
            {
                "func": tasks.dialogue,
                "trigger": "cron",
                "hour": "*/3",
            },
        ],
    )

    services: list[Service] = [
        scheduler_service,
        Admin(
            address=args.api_address,
            port=args.api_port,
        ),
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
