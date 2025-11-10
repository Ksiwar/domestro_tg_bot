import logging
from aiogram import Router, F
from aiogram.types import Message, Contact
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from models.user import User
from utils.keyboards import type_device, menu

LIST_USER = []
router = Router()

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

END_MASSAGE = """
Вы получили приветственные 10 слотов для контроля доступности! 😎

Вы можете использовать их для отслеживания 5-ти устройств и 5-ти онлайн-сервисов.

Чтобы добавить новое устройство или сервис выберите подходящий тип.

Вы также можете выбрать нужную функцию в Меню.
"""
HARDCODED_SERVICE = {
    "Битрикс24": "www.bitrix24.ru",
    "AmoCRM": "www.amocrm.ru",
    "RetailCRM": "www.retailcrm.ru",
    "1С:CRM": "1c.ru",
    "Мегаплан": "megaplan.ru",
    "Простой бизнес": "www.prostoy.ru",
    "EnvyCRM": "envycrm.com"
}

@router.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):
    contact: Contact = message.contact
    try:
        new_user = User(chat_id=message.chat.id, first_name=contact.first_name, last_name=contact.last_name, name=message.from_user.username, phone_number=contact.phone_number)
        await state.update_data(user=new_user.model_dump(), HARDCODED_SERVICE=HARDCODED_SERVICE)
        await message.answer("✅ Авторизация прошла успешно!", reply_markup=menu())
        await message.answer(END_MASSAGE, parse_mode="Markdown", reply_markup=type_device())
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")