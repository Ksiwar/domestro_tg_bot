from aiogram.types import  InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from .constants import MAIN_BUTTON, BUTTON_NAME

def list_devices(user) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if user != None:
        for index, ip_d in enumerate(user.ips):
            status ="🟢" if ip_d.is_available else "🔴"
            builder.button(text=f"{status} {ip_d.name}", callback_data="ip_"+ str(index))
        for index, service in enumerate(user.service):
            status ="🟢" if service.is_available else "🔴"
            builder.button(text=f"{status} {service.name}", callback_data="host_" + str(index))
   
    builder.button(text="Добавить ➕", callback_data="add")
    return builder.adjust(1).as_markup(resize_keyboard=True)

def add_devices() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить ➕", callback_data="yes_IP")
    builder.button(text="Список", callback_data="not")
    return builder.adjust(2).as_markup(resize_keyboard=True)

def add_service() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить ➕", callback_data="service")
    builder.button(text="Список", callback_data="not")
    return builder.adjust(2).as_markup(resize_keyboard=True)


def add_keyboard(user) -> InlineKeyboardMarkup:
    key_board_buttons = []
    if len(user.ips) < 5:
        key_board_buttons.append(InlineKeyboardButton(text="Устройства", callback_data="ip"))
    if len(user.service) < 5:
        key_board_buttons.append(InlineKeyboardButton(text="Сервис", callback_data="service"))

    return InlineKeyboardMarkup(inline_keyboard=[
        key_board_buttons,
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])

def ip_or_name(type) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if type=="IP":
        builder.button(text="IP", callback_data="rename_ip")
    else:
        builder.button(text="Сервис", callback_data="edit_url"+type)

    builder.button(text="Имя", callback_data="edit_name")
    return builder.adjust(2).as_markup(resize_keyboard=True)

def list_service(HARDCODED_SERVICE) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, _url in HARDCODED_SERVICE.items():
        builder.button(text=str(name), callback_data=f"service_add_{str(name)}")
    builder.button(text="Другой сервис", callback_data="other_service")
    return builder.adjust(1).as_markup(resize_keyboard=True)

def options() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data="edit"), InlineKeyboardButton(text="Удалить", callback_data="delete_ip"),],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])

def back() -> InlineKeyboardMarkup:
     return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back")]])

def options_service(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть", url=url)],
        [InlineKeyboardButton(text="Редактировать", callback_data="edit"), InlineKeyboardButton(text="Удалить", callback_data="delete_service")],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])


def type_device() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Устройства", callback_data="ip"), InlineKeyboardButton(text="Сервис", callback_data="service"),]
    ])

def options() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data="edit"), InlineKeyboardButton(text="Удалить", callback_data="delete_ip"),],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])


# (кнопка :  "🔓 Выбрать Premium")
# (когда пользователь жмет на кнопку )
def choose_premium() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Выбрать Premium", callback_data="premium")],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])


def leave_suggestions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Оставить предложение", callback_data="feedback")],
        [InlineKeyboardButton(text="✨ Все отлично, спасибо!", callback_data="feedback_thanks")],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])

def menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=MAIN_BUTTON)],
        [KeyboardButton(text=BUTTON_NAME)]
    ], resize_keyboard=True)