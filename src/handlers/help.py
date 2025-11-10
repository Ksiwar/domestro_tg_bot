import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = Router()

@router.message(Command("help"))
async def cmd_start(message: Message):
    await message.answer("В разработке", parse_mode="Markdown")

