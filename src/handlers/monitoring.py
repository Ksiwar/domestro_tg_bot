import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from copy import deepcopy
from models.user import Ip, User, Service, NameNotUniqueError, IpNotUniqueError, HostNotUniqueError
from pydantic import BaseModel, field_validator, ValidationError 
from utils.keyboards import list_service, options, options_service, list_devices, add_keyboard, add_devices, \
    add_service, choose_premium
from utils.constants import MAIN_BUTTON, UN_AUTH, HOST_VALIDATION
from .premium import MAX_DEVICE_ADDED, MAX_IPS_ADDED, MAX_SERVICE_ADDED

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
router = Router()

HELLO_MESSAGE = """Вот список устройств и сервисов:"""
SUCCESSES_EDIT = """Отлично! Данные обновлены!"""

NOT_UNIQUE_NAME = "🚫 Название для устройства не является уникальным. 😕\n Повторите ввод используя уникальное имя."
NOT_UNIQUE_IPS_NAME = "🚫 Название для устройства не является уникальным. 😕\n  Повторите ввод используя уникальное имя."
NOT_UNIQUE_SERVICE_NAME = "🚫 Название для сервиса не является уникальным. 😕\n  Повторите ввод используя уникальное имя."
NOT_UNIQUE_IP = "🚫 IP для устройства не является уникальным. 😕\n Повторите ввод используя уникальное имя."
NOT_UNIQUE_HOST = "🚫 URL для сервиса не является уникальным. 😕\n Повторите ввод используя уникальное имя."


# Define states
class Form(StatesGroup):
    waiting_for_ip = State()
    waiting_for_url = State()
    waiting_for_name_url = State()
    waiting_edit = State()
    waiting_for_name_ip = State()
    add_one_more_url = State()
    add_one_more_ip = State()


@router.message(Command("monitoring"))
async def cmd_monitoring(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(state=None)
    if data.get("user"):
        user = User(**data["user"])
        await message.answer(HELLO_MESSAGE, reply_markup=list_devices(user))
        return

    await message.answer(UN_AUTH)

@router.message(F.text == MAIN_BUTTON)
async def cmd_monitoring(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(state=None)
    if data.get("user"):
        user = User(**data["user"])
        await message.answer(HELLO_MESSAGE, reply_markup=list_devices(user))
        return

    await message.answer(UN_AUTH)

@router.callback_query(F.data == "add")
async def cmd_add(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    if len(user.ips) + len(user.service) >= 10:
        await call.message.edit_text(MAX_DEVICE_ADDED, reply_markup=choose_premium(), parse_mode="Markdown")
        return

    await call.message.edit_text("Выберите устройcтво/сервис",
                                 reply_markup=add_keyboard(user))  # count validation in fun add_keyboard


@router.callback_query(F.data == "service")
async def cmd_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    HARDCODED_SERVICE = data["HARDCODED_SERVICE"]

    if len(user.service) >= 5:
        await call.message.edit_text(MAX_SERVICE_ADDED, reply_markup=choose_premium(), parse_mode="Markdown")
        return

    await call.message.edit_text("Список сервисов", reply_markup=list_service(HARDCODED_SERVICE))


@router.callback_query(F.data.startswith("service_add_"))
async def cmd_service_add(call: CallbackQuery, state: FSMContext):
    name = call.data[12:]
    data = await state.get_data()
    url = data["HARDCODED_SERVICE"].get(name)
    user = User(**data["user"])
    new_service = Service(name=name, host=url)

    if len(user.service) >= 5:
        await call.message.edit_text(MAX_SERVICE_ADDED, reply_markup=choose_premium(), parse_mode="Markdown")
        return

    user.add_service(service=new_service)
    await state.update_data(user=user.model_dump(),
                            HARDCODED_SERVICE=remove_service_by_name(data["HARDCODED_SERVICE"], name))
    await call.message.edit_text(f"Сервис {call.data[12:]} добавлен и поставлен на мониторинг")
    await call.message.answer(f"Хотите добавить еще сервис? Или посмотреть актуальный список?",
                              reply_markup=add_service())


@router.callback_query(F.data.startswith("host_") | F.data.startswith("ip_"))
async def open_options(call: CallbackQuery, state: FSMContext):
    type, id = ("IP", int(call.data[3:])) if call.data.startswith("ip_") else ("URL", int(call.data[5:]))
    await state.update_data(index=id)
    data = await state.get_data()
    user = User(**data["user"])
    await state.update_data(type=type, index=id)
    if type == "IP":
        if user.ips:
            status = "🟢" if user.ips[id].is_available else "🔴"
            await call.message.edit_text(
                f"{status} *Тип*: Устройство. *Название*: _{user.ips[id].name}_ \n*ip*: {user.ips[id].ip}",
                reply_markup=options(), parse_mode="Markdown")
    else:
        if user.service:
            status = "🟢" if user.service[id].is_available else "🔴"
            await call.message.edit_text(
                f"{status} *Тип*: Веб-сервис *Название*: _{user.service[id].name}_ \n*url*: {user.service[id].host}\n",
                reply_markup=options_service(user.service[id].host), parse_mode="Markdown", )


@router.callback_query(F.data.startswith("delete_"))
async def cmd_option_delete(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    index = data["index"]
    if call.data[7:] == "ip":
        user.delete_ip_by_index(index)
    else:
        HARDCODED_SERVICE = data["HARDCODED_SERVICE"]
        HARDCODED_SERVICE[user.service[index].name] = user.service[index].host
        await state.update_data(HARDCODED_SERVICE=HARDCODED_SERVICE)
        user.delete_service_by_index(index)
    await state.update_data(user=user.model_dump())
    await call.message.edit_text(HELLO_MESSAGE, reply_markup=list_devices(user))


@router.callback_query(F.data == "edit")
async def cmd_edit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    text = "IP" if data["type"] == "IP" else "Caйт"

    builder.button(text=text, callback_data="edit_ip")
    builder.button(text="Название", callback_data="edit_name")
    await call.message.edit_text(call.message.text + "\nВыберите поле, которое хотите изменить.",
                                 reply_markup=builder.adjust(2).as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("edit_"))
async def cmd_edit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    edit_fild = call.data[5:]

    if not edit_fild:
        await call.message.edit_text("Не может быть пустым. Пожалуйста, введите корректные данные.")
        return

    type = data["type"]
    fild = "name" if edit_fild == "name" else "ip" if type == "IP" else "host"
    text = "новое название" if edit_fild == "name" else "новый ip-адрес" if type == "IP" else "новый URL"
    await state.update_data(edit=fild)
    await state.set_state(Form.waiting_edit)
    await call.message.edit_text(f"Введите {text}")


@router.message(StateFilter("Form:waiting_edit"))
async def process_edit(message: Message, state: FSMContext):
    input = message.text
    if not input:
        await message.answer("Не может быть пустым. Пожалуйста, введите корректные данные.")
        return

    data = await state.get_data()
    user = User(**data["user"])
    type = data["type"]
    edit_fild = data["edit"]
    index = data["index"]
    if edit_fild == "name":
        if type == "IP":
            ips_copy = deepcopy(user.ips)
            try:
                user.update_ip_by_index(index, ips_copy[index].copy(update={"name": input}))
            except NameNotUniqueError:
                await message.answer(NOT_UNIQUE_IPS_NAME)
                await state.set_state(Form.waiting_edit)
                return
            except IpNotUniqueError:
                await message.answer(NOT_UNIQUE_IP)
                await state.set_state(Form.waiting_edit)
                return

            await state.update_data(user=user.model_dump())
            await message.answer(f"Вы ввели название: *{input}* \n{SUCCESSES_EDIT}", parse_mode="Markdown")
            await message.answer(HELLO_MESSAGE, reply_markup=list_devices(user))
            await state.set_state(state=None)
            return

        service_copy = deepcopy(user.service)
        try:
            user.update_service_by_index(index, service_copy[index].copy(update={"name": input}))
        except NameNotUniqueError:
            await message.answer(NOT_UNIQUE_SERVICE_NAME)
            await state.set_state(Form.waiting_edit)
            return
        except HostNotUniqueError:
            await message.answer(NOT_UNIQUE_HOST)
            await state.set_state(Form.waiting_edit)
            return

        await state.update_data(user=user.model_dump())
        await message.answer(f"Вы ввели название: *{input}* \n{SUCCESSES_EDIT}", parse_mode="Markdown")
        await message.answer(HELLO_MESSAGE, reply_markup=list_devices(user))
    elif edit_fild == "ip":
        ips_copy = deepcopy(user.ips)
        try:
            updated_ip = ips_copy[index].copy(update={"ip": input})
            Ip.model_validate(updated_ip.model_dump())
            user.update_ip_by_index(index, updated_ip)
        except ValidationError as e:
            print(f"Validation Error: {e.errors()}")
            await message.answer("Некорректный IP-адрес. Пожалуйста, введите корректный IP-адрес.")
            return
        except NameNotUniqueError:
            await message.answer(NOT_UNIQUE_IPS_NAME, parse_mode="Markdown")
            return
        except IpNotUniqueError:
            await message.answer(NOT_UNIQUE_IP, parse_mode="Markdown")
            return

        await state.update_data(user=user.model_dump())
        await message.answer(f"Вы ввели IP-адрес: {input} \n{SUCCESSES_EDIT}")
        await message.answer(HELLO_MESSAGE, reply_markup=list_devices(user))
    elif edit_fild == "host":
        service_copy = deepcopy(user.service)
        try:
            update_service =service_copy[index].copy(update={"host": input})
            Service.model_validate(update_service.model_dump())
            user.update_service_by_index(index, update_service)
        except NameNotUniqueError:
            await message.answer(NOT_UNIQUE_SERVICE_NAME)
            return
        except HostNotUniqueError:
            await message.answer(NOT_UNIQUE_HOST)
            return
        except ValidationError:
            await message.answer(HOST_VALIDATION, parse_mode="Markdown")
            return

        await state.update_data(user=user.model_dump())
        await message.answer(f"Вы ввели сервис: {input} \n{SUCCESSES_EDIT}")
        await message.answer(HELLO_MESSAGE, reply_markup=list_devices(user))
    await state.set_state(state=None)


@router.callback_query(F.data == "back")
async def cmd_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(state=None)
    user = User(**data["user"])
    await state.update_data(user=user.model_dump())
    await call.message.edit_text(HELLO_MESSAGE, reply_markup=list_devices(user))


@router.callback_query(F.data == "other_service")
async def other_service(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_name_url)
    await call.message.edit_text("""Пожалуйста, введите URL сервиса,\nкоторый вы хотите добавить для отслеживания""",
                                 parse_mode="Markdown")


@router.callback_query(F.data == "ip")
async def cmd_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_name_ip)
    await call.message.edit_text("Пожалуйста, введите IP-адрес устройства, которое Вы хотите добавить под контроль.")


@router.message(StateFilter("Form:waiting_for_name_ip"))
async def process_ip(message: Message, state: FSMContext):
    ip_address = message.text
    data = await state.get_data()
    user = User(**data["user"])
    if not ip_address:
        await message.answer("Ip-адрес не может быть пустым. Пожалуйста, введите корректный Ip-адрес.")
        return

    try:
        ip_model = Ip(ip=ip_address, name="")
        user.add_ip(ip_model)
    except ValidationError:
        await message.answer("Некорректный IP-адрес. Пожалуйста, введите корректный IP-адрес.")
        return
    except NameNotUniqueError:
        await message.answer(NOT_UNIQUE_IPS_NAME)
        return
    except IpNotUniqueError:
        await message.answer(NOT_UNIQUE_IP)
        return
        

    await state.update_data(new_ip=ip_model.model_dump())
    await state.set_state(Form.add_one_more_ip)
    await message.answer(f"Вы ввели IP-адрес: {ip_address} \nЗадайте название устройству")


@router.message(StateFilter("Form:waiting_for_name_url"))
async def process_url(message: Message, state: FSMContext):
    url = message.text
    data = await state.get_data()
    user = User(**data["user"])
    if not url:
        await message.answer("URL не может быть пустым. Пожалуйста, введите корректный URL.")
        return

    try:
        service = Service(host=url, name="")
        user.add_service(service)
    except ValidationError:
        await message.answer(HOST_VALIDATION, parse_mode="Markdown")
        return
    except NameNotUniqueError:
        await message.answer(NOT_UNIQUE_IPS_NAME)
        return
    except IpNotUniqueError:
        await message.answer(NOT_UNIQUE_IP)
        return

    await state.update_data(service=service.model_dump())
    await state.set_state(Form.add_one_more_url)
    await message.answer(f"Вы ввели сервис: {url} \nЗадайте название сервису")    


@router.message(StateFilter("Form:add_one_more_ip"))
async def process_ip_name(message: Message, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    name = message.text
    if not name:
        await message.answer("Название не может быть пустым. Пожалуйста, введите корректное название.")
        return

    ip = Ip(**data["new_ip"])
    new_ip = ip.model_copy(update={"name": name})

    try:
        user.add_ip(new_ip)
    except NameNotUniqueError:
        await message.answer(NOT_UNIQUE_IPS_NAME)
        await state.set_state(Form.add_one_more_ip)
        return
    except IpNotUniqueError:
        await message.answer(NOT_UNIQUE_IP)
        await state.set_state(Form.add_one_more_ip)
        return

    await state.update_data(user=user.model_dump())
    sucsess = f"Контроль доступности устройства *{name}* успешно начат! 🎉"
    text = f"Хотите добавить еще устройство? Или посмотреть актуальный список?"
    await state.set_state(state=None)
    await message.answer(sucsess, parse_mode="Markdown")
    await message.answer(text, parse_mode="Markdown", reply_markup=add_devices())


@router.message(StateFilter("Form:add_one_more_url"))
async def process_service_name(message: Message, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    name = message.text
    if not name:
        await message.answer("Название не может быть пустым. Пожалуйста, введите корректное название.")
        return
    service = Service(**data["service"])
    new_service = service.model_copy(update={"name": name})

    try:
        user.add_service(service=new_service)
    except NameNotUniqueError:
        await message.answer(NOT_UNIQUE_SERVICE_NAME)
        await state.set_state(Form.add_one_more_url)
        return
    except HostNotUniqueError:
        await message.answer(NOT_UNIQUE_HOST)
        await state.set_state(Form.add_one_more_url)
        return

    await state.update_data(user=user.model_dump())
    await state.set_state(state=None)
    await message.answer(f"Контроль доступности сервиса *{name}* успешно начат! 🎉", parse_mode="Markdown")
    await message.answer(f"Хотите добавить еще сервис? Или посмотреть актуальный список?", parse_mode="Markdown",
                         reply_markup=add_service())


@router.callback_query(F.data.startswith("yes_"))
async def cmd_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    type = call.data[4:]

    if len(user.service) >= 5 and type == "URL":
        await call.message.edit_text(MAX_SERVICE_ADDED, reply_markup=choose_premium(), parse_mode="Markdown")
        return

    if len(user.ips) >= 5:
        await call.message.edit_text(MAX_IPS_ADDED, reply_markup=choose_premium(), parse_mode="Markdown")
        return

    new_state = Form.waiting_for_name_url if type == "URL" else Form.waiting_for_name_ip
    text = "Введите cсылку сервиса" if type == "URL" else "Введите ip-адрес"
    await state.set_state(new_state)
    await call.message.edit_text(text)


@router.callback_query(F.data == "not")
async def cmd_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = User(**data["user"])
    await state.update_data(user=user.model_dump())
    await call.message.edit_text(HELLO_MESSAGE, reply_markup=list_devices(user))


def remove_service_by_name(service_dict, name):
    """
    Удаляет сервис из словаря по имени.

    :param service_dict: Словарь с сервисами.
    :param name: Название сервиса, который нужно удалить.
    :return: Обновленный словарь.
    """
    if name in service_dict:
        del service_dict[name]
    return service_dict
