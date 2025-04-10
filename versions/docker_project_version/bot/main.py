import json
import os
import math
import logging
import asyncio
from typing import Dict, Any
import requests
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.storage.memory import MemoryStorage

# Инициализация токенов

telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
notion_token = os.getenv("NOTION_TOKEN")
support_page_id = os.getenv("SUPPORT_PAGE_ID")
#common_questions_page_id = os.getenv("COMMON_QUESTION_PAGE_ID")

# Обработчик следования пользователя
user_router = Router()

# Логирование состояний
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=telegram_bot_token)

# Диспетчер
dp = Dispatcher(storage=MemoryStorage())

# Регистрация маршрутизатора
dp.include_router(user_router)

# Загрузка данных из файла

async def load_data(data_file):
    try:
        with open(data_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # Если файл не существует, возвращаем пустой список

#Загрузка страницы общих вопросов
common_questions_page_id = asyncio.run(load_data(f"emb_info.json")).get("common_questions").get("page_id")

#Глобальные функции для получения внешних данных

#Функция для получения данных поддержки

async def get_pages(page_id, headers, num_pages=None):
    url = f"https://api.notion.com/v1/databases/{page_id}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages
    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    results = data["results"]

    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{page_id}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

async def get_chat_info(page_id):
    token = notion_token
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    page = await get_pages(page_id, headers)
    chat_info = []
    props = page[0]["properties"]
    Chat_name = props.get("Chat_name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
    workers = props.get("Workers", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
    chat_id = props.get("Chat_ID", {}).get("number", 0)
    chat_info.append([Chat_name, workers, chat_id])
    get_chat_id(chat_info[0])

# Функция получения списка вопросов

async def get_questions(fac_page_id):
    token = notion_token
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    index = 1
    list_str_questions = []
    for page_id in [common_questions_page_id, fac_page_id]:
        pages = await get_pages(page_id, headers)
        for i, page in enumerate(pages):
            props = page["properties"]
            question = "".join(
                [part.get("text", {}).get("content", "") for part in props.get("Вопрос", {}).get("title", [])])
            list_str_questions.append(f"*{index + i}) *" + f"_{question}_")
        index+=len(pages)
    return list_str_questions

async def search(user_question: str, faculty_name: str) -> Dict[str, Any]:
    """
    Новая функция для запроса к модели через API
    """
    model_url = os.getenv("MODEL_API_URL")
    api_token = os.getenv("API_TOKEN")
    if not model_url or not api_token:
        logging.error("API configuration missing")
        return {
            "question": user_question,
            "score": 0,
            "error": "Configuration error",
            "answer": "Сервер не отвечает",
        }

    payload = {
        "question": user_question,
        "faculty_name": faculty_name,  # Название факультета
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{model_url}?token={api_token}",
                    json=payload,
                    timeout=10
            ) as response:

                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logging.error(f"Model API error: {response.status} - {error_text}")
                    return {
                        "question": user_question,
                        "score": 0,
                        "error": f"API error {response.status}",
                        "answer": "Извините, сервис временно недоступен"
                    }

    except asyncio.TimeoutError:
        logging.error("Model API timeout")
        return {
            "question": user_question,
            "score": 0,
            "error": "Timeout",
            "answer": "Сервис не отвечает, попробуйте позже"
        }
    except Exception as e:
        logging.error(f"Connection error: {str(e)}")
        return {
            "question": user_question,
            "score": 0,
            "error": f"Connection error: {str(e)}",
            "answer": "Ошибка соединения с сервисом"
        }

# Классы States

class MainStates(StatesGroup):
    start_state = State()
    problem_types = State()

class Faculties(StatesGroup):
    request_allocation = State()
    get_faculty = State()
    send_answer = State()

class Support(StatesGroup):
    get_id = State()
    back_request = State()
    feedback_answer = State()
    check_answer = State()
    status_answer = State()


# Клавиатуры

#Клавиатуры стандартного меню

def get_started():
    keyboard_list = [
        [InlineKeyboardButton(text="Начать работу 🚀", callback_data='Начать работу')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

def get_faculty():
    keyboard_list = [
        [InlineKeyboardButton(text='Факультет информатики, математики и компьютерных наук 💻', callback_data='fac_it')],
        [InlineKeyboardButton(text='Факультет гуманитарных наук 📚', callback_data='fac_gum')],
        [InlineKeyboardButton(text='Факультет менеджмента 📊', callback_data='fac_man')],
        [InlineKeyboardButton(text='Факультет права ⚖️', callback_data='fac_law')],
        [InlineKeyboardButton(text='Факультет экономики 💼', callback_data='fac_econ')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

def get_main_options_choice():
    keyboard_list = [
        [InlineKeyboardButton(text='Задать вопрос ❓', callback_data='ask_question')],
        [InlineKeyboardButton(text='Список вопросов 📜', callback_data='question_list')],
        [InlineKeyboardButton(text='Обратиться в службу поддержки 💬', callback_data='support')],
        [InlineKeyboardButton(text='Назад 🏠', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

def get_outback_options():
    keyboard_list = [
        [InlineKeyboardButton(text='Назад 🏠', callback_data='back')],
        [InlineKeyboardButton(text='Задать еще вопрос ❓', callback_data='ask_question')],
        [InlineKeyboardButton(text='Я не получил нужного ответа ❌', callback_data='support')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

# Клавиатуры сегмента Службы поддержки

def support_options():
    keyboard_list = [
        [InlineKeyboardButton(text='Написать запрос ✍️', callback_data='write_request')],
        [InlineKeyboardButton(text='Назад 🏠', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

def support_users_options():
    keyboard_list = [
        [InlineKeyboardButton(text='Отправить запрос 📤', callback_data='send_request')],
        [InlineKeyboardButton(text='Перезаписать вопрос ✍️', callback_data='write_request')],
        [InlineKeyboardButton(text='Назад 🏠', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

def user_mark():
    keyboard_list = [
        [InlineKeyboardButton(text='Вопрос решен ✅', callback_data='accepted')],
        [InlineKeyboardButton(text='Я не получил нужного ответа ❌', callback_data='not_accepted')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard

def check_answer():
    keyboard_list = [
        [InlineKeyboardButton(text='Отправить ответ 📤', callback_data='send_answer')],
        [InlineKeyboardButton(text='Перезаписать ответ ✍️', callback_data='write_again')],
        [InlineKeyboardButton(text='Назад 🏠', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


# Команды


#Команда /start

@user_router.message(Command("start"))
async def start_process(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        first_message = await message.answer(f"*Привет, вышкинец!*" + "\n\n" +
                                             f"Я бот, в котором ты можешь получить ответ на все интересующие тебя вопросы по поводу обучения в Вышке." + "\n\n" +
                                             f"*А также получить оперативный ответ от представителей службы поддержки Вышки.*",
                                             reply_markup=get_started(), parse_mode="Markdown")
        await state.update_data(last_message_id=first_message.message_id)
        await state.update_data(message_edit = first_message)
    await state.set_state(MainStates.start_state)

#Команда для ответа на запрос пользователя

@user_router.message(Command("feedback_message"))
async def start_process_feed(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        await get_chat_info(support_page_id)
        if message.chat.id == chat_information[2]:
            feedback_message = await message.answer(f"Пришлите" + f"* ID студента,*" + f" которому отвечаете.",
                                                    parse_mode="Markdown")
            await state.update_data(last_message_id=feedback_message.message_id)
            await state.set_state(Support.get_id)

#Команда для отправки запроса в поддержку

@user_router.message(Command("request_to_kko"))
async def access_message(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        await get_chat_info(support_page_id)
        feedback_answer = await message.answer(f"*В данном отделе бота *" + f"ты можешь отправить запрос в " + f"*поддержку.*" + "\n\n" +
                                        f"*Это стоит делать*" + f" в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях.",
                                               reply_markup=support_options(), parse_mode="Markdown")
        await state.update_data(last_message_id=feedback_answer.message_id)
        await state.set_state(Support.back_request)


# States

@user_router.callback_query(F.data == 'Начать работу', MainStates.start_state)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_edit = data.get("message_edit")
    await asyncio.sleep(0.5)
    faculty_question = await message_edit.edit_text(f"Выбери свой факультет: ",
                                                    reply_markup = get_faculty(), parse_mode = "Markdown")
    await state.update_data(last_message_id=faculty_question.message_id)
    await state.set_state(MainStates.problem_types)

#Сегмент работы с факультетами

@user_router.callback_query(F.data.count("fac"), MainStates.problem_types)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id = call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + "связанный с выбранным факультетом "
                                         + f"*или обратиться *" + f"службу поддержки?"
                              , reply_markup = get_main_options_choice(),parse_mode="Markdown")
    await state.update_data(last_message_id = main_choice.message_id)
    await state.update_data(faculty_name = call.data)
    await state.set_state(Faculties.request_allocation)

@user_router.callback_query(F.data == 'back', Faculties.request_allocation)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    back_message = await call.message.answer(f"Выбери свой факультет: ",
                                                   reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=back_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'ask_question', Faculties.request_allocation)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_to_edit = data.get("message_to_edit")
    last_message_id = data.get("last_message_id")
    if message_to_edit:
        answer_text = data.get("answer_for_question")
        await message_to_edit.edit_text(text = f"Найденная информация: \n\n" + answer_text, reply_markup = None, parse_mode = "Markdown")  # Удаление последнего сообщения
    else:
        if last_message_id:
            await asyncio.sleep(0.5)
            await bot.delete_message(chat_id=call.from_user.id,
                                    message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"Напиши свой вопрос. " + "\n\n" +
                                                 f"*Пример: *" + f"Получить справку об обучении КНТ.", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties.send_answer)

@user_router.callback_query(F.data == "rephrase", Faculties.request_allocation)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"Напиши свой вопрос. " + "\n\n" +
                                                 f"*Пример: *" + f"Получить справку об обучении КНТ.", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties.send_answer)


@user_router.message(F.text, Faculties.send_answer)
async def answer_options(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        data = await state.get_data()
        faculty_name = data.get("faculty_name")
        ai_thinking_message = await message.answer(f"_Поиск ответа в базе данных_", parse_mode="Markdown")
        info_for_answer = await search(message.text, faculty_name)
        await ai_thinking_message.delete()
        if info_for_answer.get("error") is not None:
            await message.answer("Произошла ошибка, сервис недоступен", parse_mode="Markdown")
            await asyncio.sleep(0.5)
            main_choice = await message.answer(f"*Вы хотите задать вопрос *" + "связанный с выбранным факультетом "
                                                    + f"*или обратиться *" + f"службу поддержки?"
                                                    , reply_markup=get_main_options_choice(), parse_mode="Markdown")
            await state.update_data(last_message_id=main_choice.message_id)
            await state.set_state(Faculties.request_allocation)
            return
        answer_bot_message = await message.answer(f"Найденная информация: \n\n" + info_for_answer.get("answer"),
                                          reply_markup=get_outback_options(), parse_mode="Markdown")
        await state.update_data(message_to_edit = answer_bot_message)
        await state.update_data(answer_for_question = info_for_answer.get("answer"))
        await state.set_state(Faculties.request_allocation)


@user_router.callback_query(F.data == 'support', Faculties.request_allocation)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    message_to_edit = data.get("message_to_edit")
    if message_to_edit:
        answer_text = data.get("answer_for_question")
        await message_to_edit.edit_text(text = f"Найденная информация: \n\n" + answer_text, reply_markup = None, parse_mode = "Markdown")  # Удаление последнего сообщения
    else:
        if last_message_id:
            await asyncio.sleep(0.5)
            await bot.delete_message(chat_id=call.from_user.id,
                                    message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    await get_chat_info(support_page_id)
    support_message = await call.message.answer(f"*В данном отделе бота *" + f"ты можешь отправить запрос в " + f"*службу поддержки Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f" в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях.",
                                            reply_markup=support_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=support_message.message_id)
    await state.set_state(Support.back_request)

@user_router.callback_query(F.data == 'question_list', Faculties.request_allocation)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    faculty_name = data.get("faculty_name")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    wait_message = await call.message.answer(f"_Формирую список доступных вопросов..._", parse_mode="Markdown")
    info_fac = await load_data(f"emb_info.json")
    list_of_questions = await get_questions(info_fac[faculty_name]["page_id"])
    await wait_message.delete()
    await asyncio.sleep(0.5)
    for i in range(math.ceil(len(list_of_questions) / 50)):
        start_index = i * 50
        end_index = start_index + 50
        question_chunk = list_of_questions[start_index:end_index]
        question_string = '\n'.join(question_chunk)
        await call.message.answer(f"{question_string}", parse_mode="Markdown")
    question_list_message = await call.message.answer(f"*Вы хотите задать вопрос *" + f"связанный с выбранным факультетом "
                                                 + f"*или обратиться *" + f"службу поддержки?"
                                                 , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_list_message.message_id)
    await state.set_state(Faculties.request_allocation)

# Раздел работы поддержки

@user_router.message(F.text, Support.get_id)
async def get_id(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        data = await state.get_data()
        request_message = await message.answer( f"Пришлите " + f"*ответ на запрос*" + f" студента в формате одного сообщения.",
                                       parse_mode="Markdown")
        await state.update_data(last_message_id=request_message.message_id)
        await state.update_data(user_id = int(message.text))
        await state.set_state(Support.check_answer)

@user_router.message(F.text, Support.check_answer)
async def check_answer(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        data = await state.get_data()
        last_message_id = data.get("last_message_id")
        user_id = data.get("user_id")
        if last_message_id:
            await bot.delete_message(chat_id=message.from_user.id,
                                     message_id=last_message_id)  # Удаление последнего сообщения
        check_message = await message.answer(f"Ваш ответ на запрос: " + "\n\n" + f"{message.text}" + '\n\n' + f"*ID студента: *" + "\n" + str(
                                        user_id),
                                             reply_markup=support_users_options(), parse_mode="Markdown")
        await state.update_data(ans_message = message.text)
        await state.update_data(last_message_id=check_message.message_id)
        await state.set_state(Support.status_answer)

@user_router.callback_query(F.data == 'send_answer', Support.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    ans_message = data.get("ans_message")
    user_id = data.get("user_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    await call.message.answer(f"_Ваш ответ на запрос отправлен._",
                                          parse_mode="Markdown")
    await bot.send_message(user_id, f"*Ответ на запрос от службы поддержки: *" + "\n\n" + f"{ans_message}",
                         reply_markup=user_mark(), parse_mode="Markdown")
    await state.set_state(Support.feedback_answer)

@user_router.callback_query(F.data == 'write_again', Support.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    request_message = await bot.send_message(chat_information[2], f"Пришлите " + f"*ответ на запрос*" + f" студента в формате одного сообщения.",
                                           parse_mode="Markdown")
    await state.update_data(last_message_id=request_message.message_id)
    await state.set_state(Support.check_answer)

@user_router.callback_query(F.data == 'write_again', Support.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=call.chat.id):
        data = await state.get_data()
        last_message_id = data.get("last_message_id")
        if last_message_id:
            await bot.delete_message(chat_id=call.from_user.id,
                                     message_id=last_message_id)  # Удаление последнего сообщения
        request_message = await bot.send_message(chat_information[2],
                                                 f"Пришлите " + f"*ответ на запрос*" + f" студента в формате одного сообщения.",
                                                 parse_mode="Markdown")
        await state.update_data(last_message_id=request_message.message_id)
        await state.set_state(Support.check_answer)

@user_router.callback_query(F.data == 'back', Support.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    feedback_message = await bot.send_message(chat_information[2], f"Пришлите" + f"* ID студента,*" + f" которому отвечаете.",
                                                 parse_mode="Markdown")
    await state.update_data(last_message_id=feedback_message.message_id)
    await state.set_state(Support.get_id)

@user_router.callback_query(F.data == 'accepted', Support.feedback_answer)
async def feedback_answer(call: CallbackQuery, state: FSMContext):
    await call.message.answer(f"_Рад тебе помочь!_", parse_mode="Markdown")
    next_message = await call.message.answer(f"Выбери свой факультет: ",
                                            reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=next_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'not_accepted', Support.feedback_answer)
async def feedback_answer(call: CallbackQuery, state: FSMContext):
    await call.message.answer(f"Ты можешь обратиться к одному из сотрудников" + f"* службы поддержки:*" + "\n\n" + chat_information[1],
                         parse_mode="Markdown")
    next_message = call.message.answer(f"Выбери свой факультет: ",
                                            reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=next_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'write_request', Support.back_request)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    explain_message = await call.message.answer(f"Напиши свой запрос: " + "\n\n" + f"В твоем запросе " + f"*ты должен указать*" + f" свое ФИО, факультет, учебную группу."
                                           , parse_mode="Markdown")
    await state.update_data(last_message_id=explain_message.message_id)
    await state.set_state(Support.back_request)

@user_router.message(F.text, Support.back_request)
async def request_check(message: Message, state: FSMContext):
    put_request_message(f"{message.text}")
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=message.from_user.id, message_id=last_message_id)
    await asyncio.sleep(0.5)
    request_message = await message.answer(f"Ваш запрос выглядит так: " + "\n\n" + f"{message.text}" + "\n\n" +
                                           f"*Проверьте, написали ли вы:*" + f"учебную группу, факультет, ФИО.",
                                           reply_markup=support_users_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=request_message.message_id)
    await state.set_state(Support.back_request)

@user_router.callback_query(F.data == 'back', Support.back_request)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    first_message = await call.message.answer(f"Выбери свой факультет: ", reply_markup=get_faculty(),
                                             parse_mode="Markdown")
    await state.update_data(last_message_id=first_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'send_request', Support.back_request)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    await bot.send_message(chat_information[2], f"*Запрос от студента: *" + "\n\n" + f"{request_message}" + "\n\n" + f"*ID студента: *" + "\n" + str(
                             call.message.from_user.id), parse_mode="Markdown")
    await call.message.answer(f"Ваш запрос " + f"направлен " + f"*в службу поддержки.*" + "\n\n" +
                         f"Максимальное время ответа - " + f"*2 дня.*", parse_mode="Markdown")


# Request for KKO

request_message = ""

def put_request_message(request):
    global request_message
    request_message = request

# Get chat id

chat_information = ['', '', 0]

def get_chat_id(storage_chat):
    global chat_information
    chat_information = storage_chat

# Запуск процесса поллинга новых апдейтов

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())