import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler(service):
    async def refresh_job():
        logger.info("Scheduler: starting refresh_all")
        try:
            results = await service.refresh_all()
            success = sum(1 for r in results if r.success)
            logger.info("Scheduler: refresh_all done — %d/%d succeeded", success, len(results))
        except Exception as e:
            logger.error("Scheduler: refresh_all failed: %s", e)

    scheduler.add_job(refresh_job, IntervalTrigger(hours=1), id="refresh_all", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — refresh_all runs every 1 hour")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
