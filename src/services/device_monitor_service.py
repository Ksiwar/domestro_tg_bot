import asyncio
import logging
import aiohttp
from repositories.user_repo import UserRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DeviceMonitorService:
    def __init__(self, max_concurrent_requests=100):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def _handle_failure(self, resource_info, resource_type, bot,collection, error=None):
        _id = resource_info.get("_id")
        telegram_id = resource_info.get("telegram_id")
        is_available = resource_info.get("is_available")
        index = resource_info.get("index")
        name = resource_info.get("name")
        identifier = resource_info.get("ip") or resource_info.get("host")

        if is_available == False:
            return

        # Обновляем статус в базе
        await UserRepository.update_user_status(
            collection,
            id=_id,
            index=index,
            field=resource_type,
            is_available=False
        )
        IPS = (
            f"🔴 _Устройство недоступно_\n"
            f"*Устройство*: {name}\n"
            f"*IP*: {identifier}\n"
            f"*Статус*: Не отвечает \n\n"
            f"⚠️ Проверьте подключение к сети или настройки устройства."
        )
        SERVISE = (
            f"🔴 __Сервис недоступен__\n"
            f"*Сервис*: {name}\n"
            f"*URL*: {identifier}\n"
            f"*Статус*: Не отвечает\n\n"
            f"⚠️ Проверьте подключение к сети или настройки сервиса."
        )
        # Формируем сообщение
        message = IPS if resource_type == 'ips' else SERVISE
        if error:
            logger.error(f"{message}. Ошибка: {error}")

        # Логируем и отправляем уведомление
        logger.warning(message)
        try:
            await bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {telegram_id}: {e}")

    async def _handle_success(self, resource_info, resource_type, bot,collection, error=None):
        telegram_id = resource_info.get("telegram_id")
        is_available = resource_info.get("is_available")
        name = resource_info.get("name")
        identifier = resource_info.get("ip") or resource_info.get("host")

        if is_available == True:
            return
        
        IPS = (
            f"🟢 _Устройство доступно_\n"
            f"*Устройство*: {name}\n"
            f"IP: {identifier}\n"
            f"*Статус*: Работает в штатном режиме\n\n"
            f"✅ _Ура! Устройство снова в сети. Продолжайте работать без перерывов._"
        )
        SERVISE = (
            f"🟢 _Сервис доступен__\n"
            f"*Сервис*: {name}\n"
            f"*URL*: {identifier}\n"
            f"*Статус*: Работает в штатном режиме\n\n"
            f"✅ _Ура! Сервис снова в сети. Продолжайте работать без перерывов._"
        )  
        message = IPS if resource_type == 'ips' else SERVISE
        if error:
            logger.error(f"{message}. Ошибка: {error}")

        # Логируем и отправляем уведомление
        logger.warning(message)
        try:
            await bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {telegram_id}: {e}")

    async def ping_ip(self, ip_info, bot, collection):
        async with self.semaphore:
            ip = ip_info.get("ip")
            id = ip_info.get("_id")
            try:
                # Запускаем системный ping
                proc = await asyncio.create_subprocess_exec(
                    "ping", "-c", "1", "-W", "2", ip,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode == 0:
                    logger.debug(f"Ping to {ip} successful")
                    await UserRepository.update_user_status(
                        collection,
                        id=id,
                        index=ip_info.get("index"),
                        field="ips",
                        is_available=True
                    )
                    await self._handle_success(ip_info, "ips", bot, collection, f"Exit code {proc.returncode}")
                    return True
                
                logger.error(f"Ping fail to {ip}: {str(proc.returncode)}")
                await self._handle_failure(ip_info, "ips", bot, collection, f"Exit code {proc.returncode}")
                return False

            except Exception as e:
                logger.error(f"Ping error to {ip}: {str(e)}")
                await self._handle_failure(ip_info, "ips", bot, collection, str(e))
                return False

    async def check_service(self, session, service_info, bot, collection):
        async with self.semaphore:
            host = service_info.get("host")
            url = f"http://{host}"
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        await UserRepository.update_user_status(
                            collection,
                            id=service_info.get("_id"),
                            index=service_info.get("index"),
                            field="service",
                            is_available=True
                        )
                        await self._handle_success(service_info, "service", bot, collection, "")
                        return True
                    
                    await self._handle_failure(
                        service_info, 
                        "service", 
                        bot,
                        f"HTTP status {response.status}"
                    )
                    return False
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                await self._handle_failure(service_info, "service", bot, error_msg)
                return False

    async def check_devices(self, bot, collection):
        try:
            combined_data = await UserRepository.aggregate_ips_and_services(collection)
            all_ips = combined_data.get("all_ips", [])
            logger.info(f"all_ips: {all_ips}")
            all_services = combined_data.get("all_services", [])
            logger.info(f"all_services: {all_services}")

            logger.info(f"Starting checks: {len(all_ips)} IPs, {len(all_services)} services")

            async with aiohttp.ClientSession() as session:
                results = await asyncio.gather(
                    *[self.ping_ip(ip, bot, collection) for ip in all_ips],
                    *[self.check_service(session, service, bot, collection) for service in all_services],
                    return_exceptions=True
                )

                # Log the results for debugging
                logger.debug(f"Results: {results}")

                success_count = sum(1 for r in results if r is True)
                total_count = len(results)
                success_rate = success_count / total_count if total_count > 0 else 0
                logger.info(f"Check completed. Success rate: {success_rate:.2%}")

                return {
                    "total_checked": total_count,
                    "success_rate": success_rate,
                    "details": results
                }

        except Exception as e:
            logger.error(f"Critical error in check_devices: {str(e)}")
            raise