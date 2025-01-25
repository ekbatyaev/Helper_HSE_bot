import logging
import asyncio
import re
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.storage.memory import MemoryStorage

from modules.schedule import send_schedule
from tokens_file import telegram_bot_token, notion_token

notion_token = notion_token
notion_page_id = "e4600d549cf444049fc51bdd438ad0aa"
notion_database_id = notion_page_id
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


async def get_answer(pattern, page_id):
    token = notion_token

    # page_id = "ec48b9dacec340808876fbaf0947d4e6"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    DATABASE_ID = page_id

    async def get_pages(num_pages=None):
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        get_all = num_pages is None
        page_size = 100 if get_all else num_pages
        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=headers)

        data = response.json()
        results = data["results"]

        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            results.extend(data["results"])

        return results

    async def extract_rich_text(rich_text_array):
        content = ""
        for item in rich_text_array:
            text_content = item.get("text", {}).get("content", "")
            annotations = item.get("annotations", {})

            # Применяем форматирование
            if annotations.get("bold"):
                text_content = f"*{text_content}*"
            if annotations.get("italic"):
                text_content = f"_{text_content}_"
            if annotations.get("underline"):
                text_content = f"~{text_content}~"

            content += text_content
        return content

    pages = await get_pages()
    information = []

    for page in pages:
        props = page["properties"]
        question = props.get("Вопрос", {}).get("title", [{}])[0].get("text", {}).get("content", "")
        answer = props.get("Ответ", {}).get("rich_text", [])
        formatted_answer = extract_rich_text(answer)
        information.append([0, question, formatted_answer, 0])

    async def minimum_changes(text, pattern):
        n = len(text)
        m = len(pattern)

        # Создаем таблицу для хранения результатов
        dp = [[0] * (m + 1) for _ in range(n + 1)]

        # Заполняем первую строку и первый столбец
        for i in range(n + 1):
            dp[i][0] = i  # Количество удалений, чтобы превратить текст в пустую строку
        for j in range(m + 1):
            dp[0][j] = j  # Количество вставок, чтобы превратить пустую строку в паттерн

        # Заполняем таблицу на основе динамического программирования
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if text[i - 1] == pattern[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]  # Символы совпадают, ничего не нужно менять
                else:
                    dp[i][j] = min(dp[i - 1][j] + 1,  # Удаление
                                   dp[i][j - 1] + 1,  # Вставка
                                   dp[i - 1][j - 1] + 1)  # Замена

        return dp[n][m]  # Минимальное количество изменений

    for i in range(0, len(information)):
        changes_needed = minimum_changes(information[i][1], pattern)
        information[i][0] = changes_needed
    information.sort()

    async def stem_word(word):
        # Удаляет последние 2 символа, если длина слова больше 2
        return word[:-2] if len(word) > 2 else word

    async def get_matches(pattern, text):
        # Преобразуем паттерн
        pattern = pattern.lower()
        # Удаляем окончания из слов в паттерне
        pattern_words = set(stem_word(word) for word in re.findall(r'\b\w+\b', pattern))

        # Преобразуем текст
        text = text.lower()

        text_words = set(stem_word(word) for word in re.findall(r'\b\w+\b', text))
        matches = pattern_words.intersection(text_words)
        match_count = len(matches)

        return match_count

    for i in range(0, len(information)):
        information[i][3] = get_matches(pattern, information[i][1])

    information.sort(reverse=True, key=lambda x: x[3])
    put_answer([information[0][2], information[1][2], information[2][2]])
    message_for_user = f"*Схожие вопросы: *" + "\n\n"
    for i in range(0, 3):
        message_for_user += f"*Вопрос №{i + 1}: *" + "\n" + f"_{information[i][1]}_" + '\n\n'
    return message_for_user


async def get_chat_info(page_id):
    token = "secret_N8zfGUMB144nM1TMojVYmSQtyMt2A5pu6RgyCmlcNL3"

    # page_id = "ec48b9dacec340808876fbaf0947d4e6"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    DATABASE_ID = page_id

    async def get_pages(num_pages=None):
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        get_all = num_pages is None
        page_size = 100 if get_all else num_pages
        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results = data["results"]

        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            results.extend(data["results"])

        return results

    page = await get_pages()
    chat_info = []
    props = page[0]["properties"]
    Chat_name = props.get("Chat_name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
    workers = props.get("Workers", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
    chat_id = props.get("Chat_ID", {}).get("number", 0)
    chat_info.append([Chat_name, workers, chat_id])
    get_chat_id(chat_info[0])


async def get_questions(page_id):
    token = "secret_N8zfGUMB144nM1TMojVYmSQtyMt2A5pu6RgyCmlcNL3"

    # page_id = "ec48b9dacec340808876fbaf0947d4e6"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    DATABASE_ID = page_id

    async def get_pages(num_pages=None):
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        get_all = num_pages is None
        page_size = 100 if get_all else num_pages
        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=headers)

        data = response.json()
        results = data["results"]

        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            results.extend(data["results"])

        return results

    pages = await get_pages()
    questions = []
    list_str_questions = f"*Список вопросов: *" + '\n\n'
    for page in pages:
        page_id = page["id"]
        props = page["properties"]
        question = props.get("Вопрос", {}).get("title", [{}])[0].get("text", {}).get("content", "")
        questions.append(question)
    for i in range(len(questions)):
        list_str_questions += f"*{i + 1}) *" + f"_{questions[len(questions) - i - 1]}_" + "\n"
    return list_str_questions


# Classes of States
class MainStates(StatesGroup):
    start_state = State()
    problem_types = State()


class Back_fac(StatesGroup):
    back_fac_it = State()
    back_fac_gum = State()
    back_fac_econ = State()
    back_fac_law = State()
    back_fac_man = State()


class Faculties_types(StatesGroup):
    fac_it = State()
    fac_gum = State()
    fac_econ = State()
    fac_law = State()
    fac_man = State()


class KKO_group(StatesGroup):
    get_id = State()
    back_request = State()
    correct_request = State()
    feedback_answer = State()
    check_answer = State()
    status_answer = State()


# KeyBoard
def get_started():
    keyboard_list = [
        [InlineKeyboardButton(text="Начать работу", callback_data='Начать работу')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def get_faculty():
    keyboard_list = [
        [InlineKeyboardButton(text='Факультет информатики, математики и компьютерных наук', callback_data='choice_1')],
        [InlineKeyboardButton(text='Факультет гуманитарных наук', callback_data='choice_2')],
        [InlineKeyboardButton(text='Факультет менеджмента', callback_data='choice_3')],
        [InlineKeyboardButton(text='Факультет права', callback_data='choice_4')],
        [InlineKeyboardButton(text='Факультет экономики', callback_data='choice_5')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def get_main_options_choice():
    keyboard_list = [
        [InlineKeyboardButton(text='Задать вопрос', callback_data='ask_question')],
        [InlineKeyboardButton(text='Список вопросов', callback_data='question_list')],
        [InlineKeyboardButton(text='Узнать расписание', callback_data='get_schedule')],
        [InlineKeyboardButton(text='Обратиться в ККО', callback_data='support')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def get_outback_options():
    keyboard_list = [
        [InlineKeyboardButton(text='Назад', callback_data='back')],
        [InlineKeyboardButton(text='Задать еще вопрос', callback_data='ask_question')],
        [InlineKeyboardButton(text='Я не получил нужного ответа', callback_data='support')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def choice_needed_question():
    keyboard_list = [
        [InlineKeyboardButton(text="Ответ на вопрос №1", callback_data='answer_1')],
        [InlineKeyboardButton(text="Ответ на вопрос №2", callback_data='answer_2')],
        [InlineKeyboardButton(text="Ответ на вопрос №3", callback_data='answer_3')],
        [InlineKeyboardButton(text="Список всех вопросов", callback_data='question_list')],
        [InlineKeyboardButton(text="Переформулировать вопрос", callback_data='rephrase')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def kko_options():
    keyboard_list = [
        [InlineKeyboardButton(text='Написать запрос', callback_data='write_request')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def kko_users_options():
    keyboard_list = [
        [InlineKeyboardButton(text='Отправить запрос', callback_data='send_request')],
        [InlineKeyboardButton(text='Перезаписать вопрос', callback_data='write_request')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def user_mark():
    keyboard_list = [
        [InlineKeyboardButton(text='Вопрос решен', callback_data='accepted')],
        [InlineKeyboardButton(text='Я не получил нужного ответа', callback_data='not_accepted')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


def check_answer():
    keyboard_list = [
        [InlineKeyboardButton(text='Отправить ответ', callback_data='send_answer')],
        [InlineKeyboardButton(text='Перезаписать ответ', callback_data='write_again')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard


# Commands
@user_router.message(Command("start"))
async def start_process(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        first_message = await message.answer(f"*Привет, вышкинец!*" + "\n\n" +
                                             f"_Я бот, в котором ты можешь получить ответ на все интересующие тебя вопросы по поводу обучения в Вышке._" + "\n\n" +
                                             f"*А также получить оперативный ответ от представителей ККО студсовета Вышки.*",
                                             reply_markup=get_started(), parse_mode="Markdown")
        await state.update_data(last_message_id=first_message.message_id)
        await state.update_data(message_edit = first_message)
    await state.set_state(MainStates.start_state)


@user_router.message(Command("feedback_message"))
async def start_process_feed(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        page_id = "0030e2cc086b4a9880ab236eb8228aa0"
        await get_chat_info(page_id)
        if message.chat.id == chat_information[2]:
            feedback_message = await message.answer(f"_Пришлите_" + f"* ID студента,*" + f"_ которому отвечаете._",
                                                    parse_mode="Markdown")
            await state.update_data(last_message_id=feedback_message.message_id)
            await state.set_state(KKO_group.get_id)

@user_router.message(Command("request_to_kko"))
async def access_message(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.5)
        page_id = "0030e2cc086b4a9880ab236eb8228aa0"
        await get_chat_info(page_id)
        feedback_answer = await message.answer(f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                        f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                               reply_markup=kko_options(), parse_mode="Markdown")
        await state.update_data(last_message_id=feedback_answer.message_id)
        await state.set_state(KKO_group.back_request)


# States
@user_router.callback_query(F.data == 'Начать работу',MainStates.start_state)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    message_edit = data.get("message_edit")
    await asyncio.sleep(0.5)
    faculty_question = await message_edit.edit_text(f"_Выбери свой факультет: _",
                                                    reply_markup = get_faculty(), parse_mode = "Markdown")
    await state.update_data(last_message_id=faculty_question.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'choice_1', MainStates.problem_types)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id = call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                              , reply_markup = get_main_options_choice(),parse_mode="Markdown")

    await state.update_data(last_message_id=main_choice.message_id)
    await state.set_state(Back_fac.back_fac_it)


@user_router.callback_query(F.data == 'choice_2', MainStates.problem_types)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                            + f"*или обратиться *" + f"_Комитет качества образования?_"
                                            , reply_markup=get_main_options_choice(), parse_mode="Markdown")

    await state.update_data(last_message_id=main_choice.message_id)
    await state.set_state(Back_fac.back_fac_gum)


@user_router.callback_query(F.data == 'choice_3', MainStates.problem_types)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                            + f"*или обратиться *" + f"_Комитет качества образования?_"
                                            , reply_markup=get_main_options_choice(), parse_mode="Markdown")

    await state.update_data(last_message_id=main_choice.message_id)
    await state.set_state(Back_fac.back_fac_man)


@user_router.callback_query(F.data == 'choice_4', MainStates.problem_types)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                            + f"*или обратиться *" + f"_Комитет качества образования?_"
                                            , reply_markup=get_main_options_choice(), parse_mode="Markdown")

    await state.update_data(last_message_id=main_choice.message_id)
    await state.set_state(Back_fac.back_fac_law)


@user_router.callback_query(F.data == 'choice_5', MainStates.problem_types)
async def role_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                            + f"*или обратиться *" + f"_Комитет качества образования?_"
                                            , reply_markup=get_main_options_choice(), parse_mode="Markdown")

    await state.update_data(last_message_id=main_choice.message_id)
    await state.set_state(Back_fac.back_fac_econ)

@user_router.callback_query(F.data == 'back', Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    back_message = await call.message.answer(f"_Выбери свой факультет: _",
                                                   reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=back_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'ask_question', Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties_types.fac_it)

@user_router.callback_query(F.data == 'support', Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_id = "0030e2cc086b4a9880ab236eb8228aa0"
    await get_chat_info(page_id)
    support_message = await call.message.answer(f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=kko_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=support_message.message_id)
    await state.set_state(KKO_group.back_request)

@user_router.callback_query(F.data.count("answer"), Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    num = int(F.data[-1])
    question_answer = await call.message.answer(f"*Ответ на вопрос №{num}:* " + "\n\n" + answer[num-1],
                                           reply_markup=get_outback_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_answer.message_id)
    await state.set_state(Back_fac.back_fac_it)

@user_router.callback_query(F.data == 'rephrase', Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    rephrase_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                         f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=rephrase_message.message_id)
    await state.set_state(Faculties_types.fac_it)

@user_router.callback_query(F.data == 'get_schedule', Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    rephrase_message = await call.message.answer(f"{await send_schedule()}", parse_mode="Markdown" )
    main_choice = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                            + f"*или обратиться *" + f"_Комитет качества образования?_"
                                            , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=main_choice.message_id)
    await state.set_state(Back_fac.back_fac_it)

@user_router.callback_query(F.data == 'question_list', Back_fac.back_fac_it)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_fac_id = 'ec48b9dacec340808876fbaf0947d4e6'
    await call.message.answer(f"{await get_questions(page_fac_id)}", parse_mode="Markdown")
    question_list_message = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                                 + f"*или обратиться *" + f"_Комитет качества образования?_"
                                                 , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_list_message.message_id)
    await state.set_state(Back_fac.back_fac_it)

@user_router.callback_query(F.data == 'back', Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    back_message = await call.message.answer(f"_Выбери свой факультет: _",
                                                   reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=back_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'ask_question', Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties_types.fac_gum)

@user_router.callback_query(F.data == 'support', Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_id = "0030e2cc086b4a9880ab236eb8228aa0"
    await get_chat_info(page_id)
    support_message = await call.message.answer(f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=kko_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=support_message.message_id)
    await state.set_state(KKO_group.back_request)

@user_router.callback_query(F.data.count("answer"), Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    num = int(F.data[-1])
    question_answer = await call.message.answer(f"*Ответ на вопрос №{num}:* " + "\n\n" + answer[num-1],
                                           reply_markup=get_outback_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_answer.message_id)
    await state.set_state(Back_fac.back_fac_gum)

@user_router.callback_query(F.data == 'rephrase', Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    rephrase_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                         f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=rephrase_message.message_id)
    await state.set_state(Faculties_types.fac_gum)

@user_router.callback_query(F.data == 'question_list', Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_fac_id = '6c8ce3dbf4ac4394a64fa12b4b4a30ca'
    await call.message.answer(f"{await get_questions(page_fac_id)}", parse_mode="Markdown")
    question_list_message = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                                 + f"*или обратиться *" + f"_Комитет качества образования?_"
                                                 , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_list_message.message_id)
    await state.set_state(Back_fac.back_fac_gum)

@user_router.callback_query(F.data == 'back', Back_fac.back_fac_man)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    back_message = await call.message.answer(f"_Выбери свой факультет: _",
                                                   reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=back_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'ask_question', Back_fac.back_fac_gum)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties_types.fac_man)

@user_router.callback_query(F.data == 'support', Back_fac.back_fac_man)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_id = "0030e2cc086b4a9880ab236eb8228aa0"
    await get_chat_info(page_id)
    support_message = await call.message.answer(f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=kko_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=support_message.message_id)
    await state.set_state(KKO_group.back_request)

@user_router.callback_query(F.data.count("answer"), Back_fac.back_fac_man)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    num = int(F.data[-1])
    question_answer = await call.message.answer(f"*Ответ на вопрос №{num}:* " + "\n\n" + answer[num-1],
                                           reply_markup=get_outback_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_answer.message_id)
    await state.set_state(Back_fac.back_fac_man)

@user_router.callback_query(F.data == 'rephrase', Back_fac.back_fac_man)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    rephrase_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                         f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=rephrase_message.message_id)
    await state.set_state(Faculties_types.fac_man)

@user_router.callback_query(F.data == 'question_list', Back_fac.back_fac_man)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_fac_id = 'e0733dd88ae5408c8d8b09c36de0097c'
    await call.message.answer(f"{await get_questions(page_fac_id)}", parse_mode="Markdown")
    question_list_message = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                                 + f"*или обратиться *" + f"_Комитет качества образования?_"
                                                 , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_list_message.message_id)
    await state.set_state(Back_fac.back_fac_man)

@user_router.callback_query(F.data == 'back', Back_fac.back_fac_law)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    back_message = await call.message.answer(f"_Выбери свой факультет: _",
                                                   reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=back_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'ask_question', Back_fac.back_fac_law)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties_types.fac_law)

@user_router.callback_query(F.data == 'support', Back_fac.back_fac_law)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_id = "0030e2cc086b4a9880ab236eb8228aa0"
    await get_chat_info(page_id)
    support_message = await call.message.answer(f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=kko_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=support_message.message_id)
    await state.set_state(KKO_group.back_request)

@user_router.callback_query(F.data.count("answer"), Back_fac.back_fac_law)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    num = int(F.data[-1])
    question_answer = await call.message.answer(f"*Ответ на вопрос №{num}:* " + "\n\n" + answer[num-1],
                                           reply_markup=get_outback_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_answer.message_id)
    await state.set_state(Back_fac.back_fac_law)

@user_router.callback_query(F.data == 'rephrase', Back_fac.back_fac_law)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    rephrase_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                         f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=rephrase_message.message_id)
    await state.set_state(Faculties_types.fac_law)

@user_router.callback_query(F.data == 'question_list', Back_fac.back_fac_law)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_fac_id = 'b86417ae42c1423e8861ff59fa6d8e8a'
    await call.message.answer(f"{await get_questions(page_fac_id)}", parse_mode="Markdown")
    question_list_message = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                                 + f"*или обратиться *" + f"_Комитет качества образования?_"
                                                 , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_list_message.message_id)
    await state.set_state(Back_fac.back_fac_law)

@user_router.callback_query(F.data == 'back', Back_fac.back_fac_econ)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    back_message = await call.message.answer(f"_Выбери свой факультет: _",
                                                   reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=back_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'ask_question', Back_fac.back_fac_econ)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    question_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=question_message.message_id)
    await state.set_state(Faculties_types.fac_econ)

@user_router.callback_query(F.data == 'support', Back_fac.back_fac_econ)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_id = "0030e2cc086b4a9880ab236eb8228aa0"
    await get_chat_info(page_id)
    support_message = await call.message.answer(f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=kko_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=support_message.message_id)
    await state.set_state(KKO_group.back_request)

@user_router.callback_query(F.data.count("answer"), Back_fac.back_fac_econ)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    num = int(F.data[-1])
    question_answer = await call.message.answer(f"*Ответ на вопрос №{num}:* " + "\n\n" + answer[num-1],
                                           reply_markup=get_outback_options(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_answer.message_id)
    await state.set_state(Back_fac.back_fac_econ)

@user_router.callback_query(F.data == 'rephrase', Back_fac.back_fac_econ)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    rephrase_message = await call.message.answer(f"_Напиши свой вопрос. _" + "\n\n" +
                                         f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode="Markdown")
    await state.update_data(last_message_id=rephrase_message.message_id)
    await state.set_state(Faculties_types.fac_econ)

@user_router.callback_query(F.data == 'question_list', Back_fac.back_fac_econ)
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    page_fac_id = '596c82e5961c46d1b34a11586eeb1cf8'
    await call.message.answer(f"{await get_questions(page_fac_id)}", parse_mode="Markdown")
    question_list_message = await call.message.answer(f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                                 + f"*или обратиться *" + f"_Комитет качества образования?_"
                                                 , reply_markup=get_main_options_choice(), parse_mode="Markdown")
    await state.update_data(last_message_id=question_list_message.message_id)
    await state.set_state(Back_fac.back_fac_econ)

@user_router.message(F.text, Faculties_types.fac_it)
async def answer_options(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        page_id_fac = 'ec48b9dacec340808876fbaf0947d4e6'
        answer_bot_message = await message.answer(f"{await get_answer(message.text, page_id_fac)}",
                                          reply_markup=choice_needed_question(), parse_mode="Markdown")
        await state.update_data(last_message_id=answer_bot_message.message_id)
        await state.set_state(Back_fac.back_fac_it)

@user_router.message(F.text, Faculties_types.fac_gum)
async def answer_options(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        page_id_fac = '6c8ce3dbf4ac4394a64fa12b4b4a30ca'
        answer_bot_message = await message.answer(f"{await get_answer(message.text, page_id_fac)}",
                                          reply_markup=choice_needed_question(), parse_mode="Markdown")
        await state.update_data(last_message_id=answer_bot_message.message_id)
        await state.set_state(Back_fac.back_fac_gum)

@user_router.message(F.text, Faculties_types.fac_man)
async def answer_options(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        page_id_fac = 'e0733dd88ae5408c8d8b09c36de0097c'
        answer_bot_message = await message.answer(f"{await get_answer(message.text, page_id_fac)}",
                                          reply_markup=choice_needed_question(), parse_mode="Markdown")
        await state.update_data(last_message_id=answer_bot_message.message_id)
        await state.set_state(Back_fac.back_fac_man)

@user_router.message(F.text, Faculties_types.fac_law)
async def answer_options(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        page_id_fac = 'b86417ae42c1423e8861ff59fa6d8e8a'
        answer_bot_message = await message.answer(f"{await get_answer(message.text, page_id_fac)}",
                                          reply_markup=choice_needed_question(), parse_mode="Markdown")
        await state.update_data(last_message_id=answer_bot_message.message_id)
        await state.set_state(Back_fac.back_fac_law)

@user_router.message(F.text, Faculties_types.fac_econ)
async def answer_options(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        page_id_fac = '596c82e5961c46d1b34a11586eeb1cf8'
        answer_bot_message = await message.answer(f"{await get_answer(message.text, page_id_fac)}",
                                          reply_markup=choice_needed_question(), parse_mode="Markdown")
        await state.update_data(last_message_id=answer_bot_message.message_id)
        await state.set_state(Back_fac.back_fac_econ)

@user_router.message(F.text, KKO_group.get_id)
async def get_id(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        get_to_user_id(int(message.text))
        request_message = await message.answer( f"_Пришлите _" + f"*ответ на запрос*" + f"_ студента в формате одного сообщения._",
                                       parse_mode="Markdown")
        await state.update_data(last_message_id=request_message.message_id)
        await state.set_state(KKO_group.check_answer)

@user_router.message(F.text, KKO_group.check_answer)
async def check_answer(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        data = await state.get_data()
        last_message_id = data.get("last_message_id")
        if last_message_id:
            await bot.delete_message(chat_id=message.from_user.id,
                                     message_id=last_message_id)  # Удаление последнего сообщения
        ans_request_message(message.text)
        check_message = await message.answer(f"_Ваш ответ на запрос: _" + "\n\n" + f"{message.text}" + '\n\n' + f"*ID студента: *" + "\n" + str(
                                        send_user_id),
                                             reply_markup=kko_users_options(), parse_mode="Markdown")
        await state.update_data(last_message_id=check_message.message_id)
        await state.set_state(KKO_group.status_answer)

@user_router.callback_query(F.data == 'send_answer', KKO_group.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    status_answer = await call.message.answer(f"_Ваш ответ на запрос отправлен._",
                                          parse_mode="Markdown")
    await call.message.answer(f"*Ответ на запрос от ККО: *" + "\n\n" + f"{ans_req_message}",
                         reply_markup=user_mark(), parse_mode="Markdown")
    await state.set_state(KKO_group.feedback_answer)

@user_router.callback_query(F.data == 'write_again', KKO_group.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    request_message = await call.message.answer(f"_Пришлите _" + f"*ответ на запрос*" + f"_ студента в формате одного сообщения._",
                                           parse_mode="Markdown")
    await state.update_data(last_message_id=request_message.message_id)
    await state.set_state(KKO_group.check_answer)

@user_router.callback_query(F.data == 'back', KKO_group.status_answer)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    feedback_message = await call.message.answer(f"_Пришлите_" + f"* ID студента,*" + f"_ которому отвечаете._",
                                            parse_mode="Markdown")
    await state.update_data(last_message_id=feedback_message.message_id)
    await state.set_state(KKO_group.get_id)

@user_router.callback_query(F.data == 'accepted', KKO_group.feedback_answer)
async def feedback_answer(call: CallbackQuery, state: FSMContext):
    await call.message.answer(f"_Рад тебе помочь!_", parse_mode="Markdown")
    next_message = await call.message.answer(f"_Выбери свой факультет: _",
                                            reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=next_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'not_accepted', KKO_group.feedback_answer)
async def feedback_answer(call: CallbackQuery, state: FSMContext):
    await call.message.answer(f"_Ты можешь обратиться к одному из сотрудников_" + f"* ККО:*" + "\n\n" + chat_information[1],
                         parse_mode="Markdown")
    next_message = call.message.answer(f"_Выбери свой факультет: _",
                                            reply_markup=get_faculty(), parse_mode="Markdown")
    await state.update_data(last_message_id=next_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'write_request', KKO_group.back_request)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    explain_message = await call.message.answer(f"_Напиши свой запрос: _" + "\n\n" + f"_В твоем запросе _" + f"*ты должен указать*" + f"_ свое ФИО, факультет, учебную группу._"
                                           , parse_mode="Markdown")
    await state.update_data(last_message_id=explain_message.message_id)
    await state.set_state(KKO_group.correct_request)

@user_router.callback_query(F.data == 'back', KKO_group.back_request)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    first_message = await call.message.answer(f"_Выбери свой факультет: _", reply_markup=get_faculty(),
                                             parse_mode="Markdown")
    await state.update_data(last_message_id=first_message.message_id)
    await state.set_state(MainStates.problem_types)

@user_router.callback_query(F.data == 'send_request', KKO_group.back_request)
async def status_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await bot.delete_message(chat_id=call.from_user.id, message_id=last_message_id)  # Удаление последнего сообщения
    await asyncio.sleep(0.5)
    await call.message.answer(f"*Запрос от студента: *" + "\n\n" + f"{request_message}" + "\n\n" + f"*ID студента: *" + "\n" + str(
                             call.message.from_user.id), parse_mode="Markdown")
    await call.message.answer(f"*Ваш запрос *" + f"_направлен _" + f"*в ККО.*" + "\n\n" +
                         f"_Максимальное время ответа - _" + f"*2 дня.*", parse_mode="Markdown")

@user_router.message(F.text, KKO_group.check_answer)
async def check_answer(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        data = await state.get_data()
        last_message_id = data.get("last_message_id")
        if last_message_id:
            await bot.delete_message(chat_id=message.from_user.id,
                                     message_id=last_message_id)  # Удаление последнего сообщения
        put_request_message(f"{message.text}")
        request_message = await message.answer(f"_Ваш запрос выглядит так: _" + "\n\n" + f"{message.text}" + "\n\n" +
                                       f"*Проверьте, написали ли вы:*" + f"_ учебную группу, факультет, ФИО._",
                                       reply_markup=kko_users_options(), parse_mode="Markdown")
        await state.update_data(last_message_id=request_message.message_id)
        await state.set_state(KKO_group.back_request)


# Answer to request
ans_req_message = ""


def ans_request_message(ans_request):
    global ans_req_message
    ans_req_message = ans_request


# Request for KKO
request_message = ""


def put_request_message(request):
    global request_message
    request_message = request


# Get to user id
send_user_id = 0


def get_to_user_id(user_id):
    global send_user_id
    send_user_id = user_id


# Get chat id
chat_information = ['', '', 0]


def get_chat_id(storage_chat):
    global chat_information
    chat_information = storage_chat


# Last answer for user
answer = ['', '', '']

def put_answer(storage):
    global answer
    answer = storage


# Messages id
messages_id = {}


def put_last_message_id(user_id, message_id):
    global messages_id
    messages_id[user_id] = message_id

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())