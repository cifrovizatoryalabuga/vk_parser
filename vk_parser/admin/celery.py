import os

from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "vk_parser",
    broker_url=os.environ.get("APP_AMQP_DSN"),
)

celery_app.autodiscover_tasks(["vk_parser.tasks"])
celery_app.conf.timezone = "Europe/Moscow"
celery_app.conf.broker_connection_retry_on_startup = True

celery_app.conf.beat_schedule = {
    "reset_send_accounts": {
        "task": "vk_parser.tasks.resetting_send_accounts_task.reset_send_accounts_task",
        "schedule": crontab(hour=14, minute=10),
    },
}
