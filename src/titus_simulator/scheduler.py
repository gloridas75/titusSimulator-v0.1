"""APScheduler integration for periodic background jobs."""

import asyncio
from datetime import date, time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from loguru import logger

from .config import Settings
from .simulator import TitusSimulator
from .state_store import StateStore


def setup_scheduler(
    app: FastAPI,
    simulator: TitusSimulator,
    store: StateStore,
    settings: Settings,
) -> AsyncIOScheduler:
    """
    Set up the APScheduler for periodic simulation cycles.
    
    Args:
        app: FastAPI application instance
        simulator: The TitusSimulator instance
        store: StateStore instance
        settings: Application settings
        
    Returns:
        Configured AsyncIOScheduler
    """
    scheduler = AsyncIOScheduler()
    
    async def scheduled_job():
        """Job that runs periodically to simulate today's events."""
        try:
            logger.info("Running scheduled simulation cycle")
            today = date.today()
            result = await simulator.run_cycle_for_date(today)
            logger.info(f"Scheduled cycle completed: {result}")
        except Exception as e:
            logger.error(f"Error in scheduled job: {e}", exc_info=True)
    
    async def cleanup_job():
        """Job that runs daily at 2 AM to cleanup old event records."""
        try:
            logger.info("Running daily cleanup job")
            deleted = await store.cleanup_old_events(days_to_keep=2)
            logger.info(f"Daily cleanup completed: {deleted} records removed")
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}", exc_info=True)
    
    # Schedule the simulation cycle at the configured interval
    scheduler.add_job(
        scheduled_job,
        trigger=IntervalTrigger(seconds=settings.poll_interval_seconds),
        id="simulation_cycle",
        name="Run simulation cycle",
        replace_existing=True,
    )
    
    # Schedule daily cleanup at 2 AM
    scheduler.add_job(
        cleanup_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_cleanup",
        name="Daily cleanup of old records",
        replace_existing=True,
    )
    
    @app.on_event("startup")
    async def start_scheduler():
        """Start the scheduler when the app starts."""
        logger.info(
            f"Starting scheduler (interval: {settings.poll_interval_seconds}s)"
        )
        scheduler.start()
        logger.info("Scheduler started")
    
    @app.on_event("shutdown")
    async def stop_scheduler():
        """Stop the scheduler when the app shuts down."""
        logger.info("Stopping scheduler")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
    
    return scheduler

