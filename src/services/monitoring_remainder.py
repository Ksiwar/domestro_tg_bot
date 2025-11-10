import asyncio
import logging
from typing import List, Dict, Any
from repositories.user_repo import UserRepository
from utils.keyboards import list_devices
from models.user import User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReminderMonitorService:
    def __init__(self, max_concurrent_requests: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def send_remainder(self, userd: dict, bot: Any) -> bool:
        """Send a reminder to a single user with rate limiting."""
        message = """Ежедневное утреннее напоминание!
Все под контролем!
😎 Вот ваш актуальный список устройств и сервисов:"""
        print(userd)
        user = User(**userd)
        print(userd)
        keyboard = list_devices(user)
        logger.info(f"Sending reminder to chat_id: {user.chat_id}")

        async with self.semaphore:
            try:
                await bot.send_message(chat_id=user.chat_id, text=message, reply_markup=keyboard)
                logger.debug(f"Successfully sent to chat_id: {user.chat_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to send to {user.chat_id}: {str(e)}")
                return False

    async def send_remainders(self, bot: Any, collection: Any) -> Dict[str, Any]:
        """Send reminders to all users with proper concurrency control."""
        try:
            users = await UserRepository.get_all_users(collection)
            logger.info(f"Starting remainder for {len(users)} users")

            # Create all tasks first
            tasks = [self.send_remainder(user, bot) for user in users]
            
            # Process results as they complete
            success_count = 0
            total_count = len(tasks)

            logger.info(f"Starting send remainder users: {total_count}")
            for future in asyncio.as_completed(tasks):
                try:
                    result = await future
                    if result:
                        success_count += 1
                except Exception as e:
                    logger.debug(f"Task failed: {str(e)}")

            success_rate = success_count / total_count if total_count > 0 else 0
            logger.info(
                f"Remainder completed. Total: {total_count}, "
                f"Success: {success_count} ({success_rate:.2%})"
            )

            return {
                "total_checked": total_count,
                "success_count": success_count,
                "success_rate": success_rate,
            }

        except Exception as e:
            logger.critical(f"Critical error in send_reminders: {str(e)}", exc_info=True)
            raise