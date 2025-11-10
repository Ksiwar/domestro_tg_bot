

import logging
from sre_parse import State
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from aiogram.filters import  StateFilter, Command
from aiogram.fsm.context import FSMContext
from utils.keyboards import leave_suggestions
from models.user import Ip, User
from aiogram.fsm.state import State, StatesGroup
from utils.constants import BUTTON_NAME, UN_AUTH

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
router = Router()

class Form(StatesGroup):
    waiting_feedback = State()


MAX_DEVICE_ADDED ="""
🚫 _Достигнут лимит устройств/сервисов_
К сожалению, на вашем текущем тарифе вы добавили максимальное количество устройств и сервисов.

Хотите продолжить мониторинг без ограничений? Перейдите на *Premium*-тариф!
"""

MAX_IPS_ADDED ="""
🚫 _Достигнут лимит устройств_
К сожалению, на вашем текущем тарифе вы добавили максимальное количество устройств и сервисов.

Хотите продолжить мониторинг без ограничений? Перейдите на *Premium*-тариф!
"""

MAX_SERVICE_ADDED ="""
🚫 _Достигнут лимит устройств_
К сожалению, на вашем текущем тарифе вы добавили максимальное количество устройств и сервисов.

Хотите продолжить мониторинг без ограничений? Перейдите на *Premium*-тариф!
"""

# (кнопка : "🔓 Выбрать Premium")
# (когда пользователь жмет на кнопку )

PREMIUM_MAX_DEVICE_ADDED_RESULT = """
🎉 _Спасибо за ваш выбор!_
Ваша заявка на переход на *Premium*-тариф успешно принята!

⏳ _Что дальше?_
Наш менеджер свяжется с вами для уточнения деталей и активации расширенных возможностей.

💡 _Хотите улучшить бота?_
Мы ценим ваше мнение! Напишите, какие функции или изменения сделают сервис удобнее для вас.

_Спасибо, что доверяете нам управление вашей сетью!_ 💻✨
"""
# (кнопки)
# 🛠 Оставить предложение
# ✨ Все отлично, спасибо!


FEED_BACK = """🚀 _Поделитесь идеей!_
Мы постоянно улучшаем сервис, и ваше мнение для нас важно!
Напишите, что бы вы хотели добавить или изменить в боте.

✍️ *Как отправить*:
Просто напишите вашу идею в чат. Мы прочитаем и учтем её в разработке!"""
FINDBACK_END = "Спасибо! Ваше предложение сохранено. Мы свяжемся с вами, если понадобятся уточнения."

# (кнопка :  "🔓 Выбрать Premium")

@router.message(Command("premium"))
async def cmd_monitoring(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(state=None)
    if not data.get("user"):
        await message.answer(UN_AUTH)
        return
    
    user = User(**data["user"])
    user.is_wants_premium = True
    await state.update_data(user=user.model_dump()),
    await message.answer(PREMIUM_MAX_DEVICE_ADDED_RESULT, reply_markup=leave_suggestions(), parse_mode="Markdown")


@router.callback_query(F.data == "premium")
async def premium(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(state=None)
    if not data.get("user"):
        await call.message.edit_text(UN_AUTH)
        return
    
    user = User(**data["user"])
    user.is_wants_premium = True
    await state.update_data(user=user.model_dump()),
    await call.message.edit_text(PREMIUM_MAX_DEVICE_ADDED_RESULT, reply_markup=leave_suggestions(), parse_mode="Markdown")

@router.callback_query(F.data == "feedback")
async def feedback(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_feedback),
    await call.message.edit_text(FEED_BACK, parse_mode="Markdown")

@router.callback_query(F.data == "feedback_thanks")
async def feedback_thanks(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    user.add_feedback("✨ Все отлично, спасибо!")
    await state.update_data(user=user.model_dump()),
    await call.message.edit_text(FINDBACK_END, parse_mode="Markdown")

@router.message(StateFilter("Form:waiting_feedback"))
async def waiting_feedback(message: Message, state: FSMContext):
    input = message.text
    if not input:
        await message.answer("Не может быть пустым. Пожалуйста, введите корректные данные.")
        return

    data = await state.get_data()
    user = User(**data["user"])

    user.add_feedback(input)
    await state.update_data(user=user.model_dump()),
    await state.set_state(state=None)
    await message.answer(FINDBACK_END, parse_mode="Markdown")


@router.message(F.text == BUTTON_NAME)
async def cmd_monitoring(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(state=None)
    if not data.get("user"):
        await message.answer(UN_AUTH)
        return
    
    await state.set_state(Form.waiting_feedback),
    await message.answer(FEED_BACK, reply_markup=leave_suggestions(), parse_mode="Markdown")

