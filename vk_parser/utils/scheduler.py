from typing import List

from aiomisc import Service
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class SchedulerService(Service):
    def __init__(self, jobs: List[dict], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheduler = AsyncIOScheduler()
        for job in jobs:
            self.scheduler.add_job(**job)

    async def start(self) -> None:
        self.scheduler.start()

    async def stop(self, exc: Exception = None) -> None:
        self.scheduler.shutdown()

    async def wait_closed(self) -> None:
        await super().wait_closed()
