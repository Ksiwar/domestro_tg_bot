import asyncio
from datetime import datetime, timezone, timedelta
import logging
from handlers import auth, start, monitoring, premium
from dotenv import load_dotenv
from services.device_monitor_service import DeviceMonitorService
from services.monitoring_remainder import ReminderMonitorService
from config.settings import Settings
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.mongo import MongoStorage
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.client.session.aiohttp import AiohttpSession

# Настройка логгера
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

def get_bot(settings: Settings) -> Bot:
    if settings.http_proxy:
        logger.info(f"Proxy Enabled")
        session = AiohttpSession(proxy=settings.http_proxy)
        return Bot(token=settings.bot_api_key, session=session)
    return Bot(token=settings.bot_api_key)

async def run_periodically(interval: int, bot, collection):
    while True:
        try:
            monitor_service = DeviceMonitorService()
            await monitor_service.check_devices(bot, collection)
        except Exception as e:
            logger.error(f"Error in periodic task: {e}")
        await asyncio.sleep(interval)

async def schedule_remainders(bot, collection):
    while True:
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)

        # If the current time is past the scheduled time, schedule for the next day
        if now >= next_run:
            next_run += timedelta(days=1)

        # Calculate the time to sleep until the next scheduled time
        time_to_sleep = (next_run - now).total_seconds()

        logger.info(f"Sleeping for {time_to_sleep} seconds until next scheduled time.")
        await asyncio.sleep(time_to_sleep)

        try:
            monitor_service = ReminderMonitorService()
            await monitor_service.send_remainders(bot, collection)
            logger.info("Reminders sent successfully.")
        except Exception as e:
            logger.error(f"Error in periodic task: {e}")

async def main():
    settings = Settings()
    bot = get_bot(settings)
    motor_client = AsyncIOMotorClient(settings.mongo_dsn)
    storage = MongoStorage(client=motor_client, db_name=settings.mongo_db_name,
                           collection_name=settings.mongo_state_collection)
    dp = Dispatcher(storage=storage)
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(auth.router)
    #dp.include_router(premium.router)
    #dp.include_router(monitoring.router) # Последовательность важна


    periodic_monitoring_task = schedule_remainders_task = None
    try:
        periodic_monitoring_task = asyncio.create_task(run_periodically(300, bot, storage._collection))
        schedule_remainders_task = asyncio.create_task(schedule_remainders(bot, storage._collection))
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if periodic_monitoring_task:
            periodic_monitoring_task.cancel()
        if schedule_remainders_task:
            schedule_remainders_task.cancel()
        await bot.session.close()
        logger.info("Resources released")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
        