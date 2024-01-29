import argparse
import logging
import os

from alembic.config import CommandLine

from vk_parser.db.utils import make_alembic_config

DEFAULT_PG_DSN = "postgresql://pguser:pgpass@127.0.0.1/pgdb"


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    alembic = CommandLine()
    alembic.parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    alembic.parser.add_argument(
        "--pg-dsn",
        default=os.getenv("APP_PG_DSN", DEFAULT_PG_DSN),
        help="Database URL [env var: APP_PG_DSN]",
    )

    options = alembic.parser.parse_args()
    if "cmd" not in options:
        alembic.parser.error("Too few arguments")
        exit(128)
    else:
        config = make_alembic_config(options)
        alembic.run_cmd(config, options)
        exit()


if __name__ == "__main__":
    main()
