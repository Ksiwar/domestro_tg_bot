import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.keyboards import type_device, menu
from models.user import User
from aiogram.fsm.context import FSMContext
from .auth import END_MASSAGE
from aiogram.types import Message

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = Router()

HELLO_MESSAGE = """
Привет!

Я Нейрончик, Ваш виртуальный помощник.
Вот что я могу:

📡 Отслеживать доступность Интернета
🖥️ Контролировать стабильность онлайн-сервисов
🔔 Уведомлять о неисправностях подключения Ваших устройств к Интернету
"""
STICKER_URL = "CAACAgIAAxkBAAEN_uBnyZhqCigkZxtHDzJBNZrI_fibMAAC-l4AAiB9SErqBjzoEsXhUDYE"


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("user"):
        user = User(**data["user"])
        if len(user.ips) == 0 and len(user.service) == 0:
            await message.answer(END_MASSAGE, parse_mode="Markdown", reply_markup=type_device())
            return

        await message.answer("Вы авторизованы!", reply_markup=menu())
        logger.info(f"Вы авторизованы!")
        return

    builder = ReplyKeyboardBuilder()
    builder.button(text="Предоставить номер телефона", request_contact=True)
    await message.answer(HELLO_MESSAGE, parse_mode="Markdown")
    await message.answer_sticker(sticker=STICKER_URL)
    await message.answer(
        "Нажмите “*Предоставить номер телефона*”, чтобы начать.",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="Markdown"
    )

