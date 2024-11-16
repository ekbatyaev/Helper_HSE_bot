import datetime
import json
import re

import telebot
from telebot import custom_filters, types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from tokens_file import telegram_bot_token
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(telegram_bot_token, state_storage=state_storage)

def get_answer(pattern, file_name):
    information = []
    data = load_data(file_name)
    for i in range(len(data)):
        information.append([0, data[i][0], data[i][1], 0])

    def minimum_changes(text, pattern):
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
                    dp[i][j] = min(dp[i - 1][j] + 1,    # Удаление
                               dp[i][j - 1] + 1,    # Вставка
                               dp[i - 1][j - 1] + 1)  # Замена

        return dp[n][m]  # Минимальное количество изменений



    for i in range(0, len(information)):
        changes_needed = minimum_changes(information[i][1], pattern)
        information[i][0] = changes_needed
    information.sort()

    def stem_word(word):
        # Удаляет последние 2 символа, если длина слова больше 2
        return word[:-2] if len(word) > 2 else word

    def get_matches(pattern, text):
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
    message_for_user =f"*Схожие вопросы: *" + "\n\n"
    for i in range(0, 3):
        message_for_user+= f"*Вопрос №{i+1}: *" + "\n" + f"_{information[i][1]}_" +'\n\n'
    return message_for_user

def get_chat_info():
    data = load_data("data/bot_work_moment.json")
    get_chat_id(["ККО", data[0][0], data[0][1]])

def get_questions(file_name):
    data = load_data(file_name)
    list_str_questions = f"*Список вопросов: *" + '\n\n'
    for i in range(len(data)):
        list_str_questions += f"*{i+1}) *" + f"_{data[len(data) - i - 1][0]}_" + "\n"
    return list_str_questions

def get_del_questions(file_name):
    data = load_data(file_name)
    list_str_questions = f"*Список вопросов: *" + '\n\n'
    for i in range(len(data)):
        list_str_questions += f"*{i}) *" + f"_{data[i][0]}_" + "\n"
    return list_str_questions

#Classes of States
class MainStates (StatesGroup):
    start_state = State()
    problem_types = State()

class Back_fac (StatesGroup):
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

class Machina_group(StatesGroup):
    choose_fac = State()
    choose_del_fac = State()
    get_question = State()
    get_ans = State()
    delete_sentence = State()

# KeyBoard
markup = types.InlineKeyboardMarkup()
item1 = types.InlineKeyboardButton("Начать работу", callback_data = 'Начать работу')
markup.add(item1)

markup1 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Факультет информатики, математики и компьютерных наук', callback_data='choice_1')
item2 = types.InlineKeyboardButton('Факультет гуманитарных наук', callback_data='choice_2')
item3 = types.InlineKeyboardButton('Факультет менеджмента', callback_data= 'choice_3')
item4 = types.InlineKeyboardButton('Факультет права', callback_data='choice_4')
item5 = types.InlineKeyboardButton('Факультет экономики', callback_data='choice_5')
markup1.add(item1, item2, item3, item4, item5)

markup2 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Задать вопрос', callback_data='ask_question')
item2 = types.InlineKeyboardButton('Список вопросов', callback_data= 'question_list')
item3 = types.InlineKeyboardButton('Обратиться в ККО', callback_data= 'support')
item4 = types.InlineKeyboardButton('Назад', callback_data= 'back')
markup2.add(item1, item2, item3, item4)

markup3 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Назад', callback_data='back')
item2 = types.InlineKeyboardButton('Задать еще вопрос', callback_data='ask_question')
item3 = types.InlineKeyboardButton('Я не получил нужного ответа', callback_data='support')
markup3.add(item1, item2, item3)

markup4 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton("Ответ на вопрос №1", callback_data = 'answer_1')
item2 = types.InlineKeyboardButton("Ответ на вопрос №2", callback_data = 'answer_2')
item3 = types.InlineKeyboardButton("Ответ на вопрос №3", callback_data = 'answer_3')
item4 = types.InlineKeyboardButton("Список всех вопросов", callback_data = 'question_list')
item5 = types.InlineKeyboardButton("Переформулировать вопрос", callback_data = 'rephrase')
markup4.add(item1, item2, item3, item4, item5)

markup5 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Написать запрос', callback_data='write_request')
item2 = types.InlineKeyboardButton('Назад', callback_data= 'back')
markup5.add(item1, item2)

markup6 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Отправить запрос', callback_data='send_request')
item2 = types.InlineKeyboardButton('Перезаписать вопрос', callback_data= 'write_request')
item3 = types.InlineKeyboardButton('Назад', callback_data= 'back')
markup6.add(item1, item2, item3)

markup7 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Вопрос решен', callback_data='accepted')
item2 = types.InlineKeyboardButton('Я не получил нужного ответа', callback_data= 'not_accepted')
markup7.add(item1, item2)

markup8 = types.InlineKeyboardMarkup(row_width = 1)
item1 = types.InlineKeyboardButton('Отправить ответ', callback_data='send_answer')
item2 = types.InlineKeyboardButton('Перезаписать ответ', callback_data= 'write_again')
item3 = types.InlineKeyboardButton('Назад', callback_data= 'back')
markup8.add(item1, item2, item3)


#Commands
@bot.message_handler(commands=['start'])
def start_message(message):


    bot_start_message = bot.send_message(message.from_user.id,f"*Привет, вышкинец!*" + "\n\n" +
                     f"_Я бот, в котором ты можешь получить ответ на все интересующие тебя вопросы по поводу обучения в Вышке._"+ "\n\n"+
                     f"*А также получить оперативный ответ от представителей ККО студсовета Вышки.*"
                     ,reply_markup=markup, parse_mode = "Markdown")

    put_last_message_id(message.from_user.id, bot_start_message.message_id)
    bot.set_state(message.from_user.id, MainStates.start_state, message.chat.id)
@bot.message_handler(commands=['feedback_message'])
def feedback_message(message):
    get_chat_info()
    if message.chat.id == chat_information[2]:
        feedback_message = bot.send_message(chat_information[2], f"_Пришлите_" + f"* ID студента,*" + f"_ которому отвечаете._", parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.get_id, chat_information[2])


@bot.message_handler(commands=['request_to_kko'])
def access_message(message):
    get_chat_info()
    feedback_message = bot.send_message(message.from_user.id,  f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                                             f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._", reply_markup = markup5, parse_mode="Markdown")
    put_last_message_id(message.from_user.id, feedback_message.message_id)
    bot.set_state(message.from_user.id, KKO_group.back_request)

@bot.message_handler(commands=['add_quest_raketa'])
def access_message(message):
    #bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    bot_first_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _",
                                               reply_markup=markup1,
                                              parse_mode="Markdown")
    put_last_message_id(message.from_user.id, bot_first_message.message_id)
    #answer_message = bot.send_message(message.from_user.id, f"_Пришлите вопрос для добавления_",parse_mode="Markdown")
    bot.set_state(message.from_user.id, Machina_group.choose_fac)

@bot.message_handler(commands=['del_quest_raketa'])
def del_message(message):
    #bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    bot_first_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _",
                                         reply_markup=markup1,
                                         parse_mode="Markdown")
    put_last_message_id(message.from_user.id, bot_first_message.message_id)
    #answer_message = bot.send_message(message.from_user.id, f"_Пришлите вопрос для добавления_",parse_mode="Markdown")
    bot.set_state(message.from_user.id, Machina_group.choose_del_fac)


#States
@bot.callback_query_handler(state=Machina_group.choose_del_fac, func = lambda callback: True)
def machina_choose_fac(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'choice_1':
        bot_choose_message = bot.send_message(message.from_user.id, f"{get_del_questions("data/fac_it.json")}" + "\n\n" + f"_Пришли индекс вопроса_", parse_mode="Markdown")
        put_file_name("data/fac_it.json")
        put_last_message_id(message.from_user.id, bot_choose_message.message_id)
        bot.set_state(message.from_user.id, Machina_group.delete_sentence)
    elif message.data == 'choice_2':
        bot_choose_message = bot.send_message(message.from_user.id,
                                              f"{get_del_questions("data/fac_gum.json")}" + "\n\n" + f"_Пришли индекс вопроса_",
                                              parse_mode="Markdown")
        put_file_name("data/fac_gum.json")
        put_last_message_id(message.from_user.id, bot_choose_message.message_id)
        bot.set_state(message.from_user.id, Machina_group.delete_sentence)
    elif message.data == "choice_3":
        bot_choose_message = bot.send_message(message.from_user.id,
                                              f"{get_del_questions("data/fac_man.json")}" + "\n\n" + f"_Пришли индекс вопроса_",
                                              parse_mode="Markdown")
        put_file_name("data/fac_man.json")
        put_last_message_id(message.from_user.id, bot_choose_message.message_id)
        bot.set_state(message.from_user.id, Machina_group.delete_sentence)
    elif message.data == "choice_4":
        bot_choose_message = bot.send_message(message.from_user.id,
                                              f"{get_del_questions("data/fac_law.json")}" + "\n\n" + f"_Пришли индекс вопроса_",
                                              parse_mode="Markdown")
        put_file_name("data/fac_law.json")
        put_last_message_id(message.from_user.id, bot_choose_message.message_id)
        bot.set_state(message.from_user.id, Machina_group.delete_sentence)
    elif message.data == "choice_5":
        bot_choose_message = bot.send_message(message.from_user.id,
                                              f"{get_del_questions("data/fac_econ.json")}" + "\n\n" + f"_Пришли индекс вопроса_",
                                              parse_mode="Markdown")
        put_file_name("data/fac_econ.json")
        put_last_message_id(message.from_user.id, bot_choose_message.message_id)
        bot.set_state(message.from_user.id, Machina_group.delete_sentence)
    else:
        bot.set_state(message.from_user.id, MainStates.problem_types)

@bot.callback_query_handler(state=Machina_group.choose_fac, func = lambda callback: True)
def machina_choose_fac(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    bot_choose_message = bot.send_message(message.from_user.id,f"_Пришлите вопрос для добавления_",
                                          parse_mode="Markdown")
    put_last_message_id(message.from_user.id, bot_choose_message.message_id)
    if message.data == 'choice_1':
        put_sentence(0, "fac_it.json")
        bot.set_state(message.from_user.id, Machina_group.get_question)
    elif message.data == 'choice_2':
        put_sentence(0, "fac_gum.json")
        bot.set_state(message.from_user.id, Machina_group.get_question)
    elif message.data == "choice_3":
        put_sentence(0, "fac_man.json")
        bot.set_state(message.from_user.id, Machina_group.get_question)
    elif message.data == "choice_4":
        put_sentence(0, "fac_law.json")
        bot.set_state(message.from_user.id, Machina_group.get_question)
    elif message.data == "choice_5":
        put_sentence(0, "fac_econ.json")
        bot.set_state(message.from_user.id, Machina_group.get_question)
    else:
        bot.set_state(message.from_user.id, MainStates.problem_types)

@bot.callback_query_handler(state=MainStates.start_state, func = lambda callback: True)
def first_message(message):
    if message.data == 'Начать работу':
        bot_first_message = bot.edit_message_text(f"_Выбери свой факультет: _", message.from_user.id, messages_id.get(message.from_user.id),  reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_first_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)

@bot.callback_query_handler(state=MainStates.problem_types, func = lambda callback: True)
def problem_types(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    bot_problem_types = bot.send_message(message.from_user.id, f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                                           ,reply_markup=markup2, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, bot_problem_types.message_id)
    if message.data == 'choice_1':
        bot.set_state(message.from_user.id, Back_fac.back_fac_it)
    elif message.data == 'choice_2':
        bot.set_state(message.from_user.id, Back_fac.back_fac_gum)
    elif message.data == "choice_3":
        bot.set_state(message.from_user.id, Back_fac.back_fac_man)
    elif message.data == "choice_4":
        bot.set_state(message.from_user.id, Back_fac.back_fac_law)
    elif message.data == "choice_5":
        bot.set_state(message.from_user.id, Back_fac.back_fac_econ)
    else:
        bot.set_state(message.from_user.id, MainStates.problem_types)
@bot.message_handler(state=Machina_group.get_question)
def get_question(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    put_sentence(1, f"{message.text}")
    get_answer_message = bot.send_message(message.from_user.id, f"_Пришлите ответ на вопрос_", parse_mode="Markdown")
    put_last_message_id(message.from_user.id, get_answer_message.message_id)
    bot.set_state(message.from_user.id, Machina_group.get_ans)

@bot.message_handler(state=Machina_group.get_ans)
def get_ans(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    put_sentence(2, f"{message.text}")
    get_answer_two_message = bot.send_message(message.from_user.id, f"_Все записано_", parse_mode="Markdown")
    add_data(sentence[0], sentence[1], sentence[2])
    print(sentence[0], sentence[1], sentence[2])
    put_last_message_id(message.from_user.id, get_answer_two_message.message_id)
    bot.set_state(message.from_user.id, MainStates.problem_types)

@bot.message_handler(state=Machina_group.delete_sentence)
def delete_sentence(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    remove_data(file_name, int(message.text))
    delete_message = bot.send_message(message.from_user.id, f"Удалено", parse_mode="Markdown")
    put_last_message_id(message.from_user.id, delete_message.message_id)
    bot.set_state(message.from_user.id, MainStates.problem_types)

@bot.callback_query_handler(state = Back_fac.back_fac_it, func = lambda callback: True)
def back_fac_it(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'back':
        bot_back_fac_it_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _", reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_back_fac_it_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'ask_question':
        bot_go_fac_it_message = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_go_fac_it_message.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_it)
    elif message.data == 'support':
        get_chat_info()
        feedback_message = bot.send_message(message.from_user.id,
                                            f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=markup5, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.back_request)
    elif message.data == 'answer_1':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №1:* " + "\n\n" + answer[0], reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_it)
    elif message.data == 'answer_2':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №2:* " + "\n\n" + answer[1],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_it)
    elif message.data == 'answer_3':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №3:* " + "\n\n" + answer[2],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_it)
    elif message.data == 'rephrase':
        rephrase_mess = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, rephrase_mess.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_it)
    elif message.data == 'question_list':
        page_fac_id = "data/fac_it.json"
        bot.send_message(message.from_user.id, f"{get_questions(page_fac_id)}", parse_mode="Markdown")
        question_list_message = bot.send_message(message.from_user.id, f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                                           ,reply_markup=markup2, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, question_list_message.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_it)

@bot.callback_query_handler(state = Back_fac.back_fac_gum, func = lambda callback: True)
def back_fac_gum(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'back':
        bot_back_fac_gum_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _", reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_back_fac_gum_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'ask_question':
        bot_go_fac_gum_message = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_go_fac_gum_message.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_gum)
    elif message.data == 'support':
        get_chat_info()
        feedback_message = bot.send_message(message.from_user.id,
                                            f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=markup5, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.back_request)
    elif message.data == 'answer_1':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №1:* " + "\n\n" + answer[0], reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_gum)
    elif message.data == 'answer_2':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №2:* " + "\n\n" + answer[1],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_gum)
    elif message.data == 'answer_3':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №3:* " + "\n\n" + answer[2],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_gum)
    elif message.data == 'rephrase':
        rephrase_mess = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, rephrase_mess.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_gum)
    elif message.data == 'question_list':
        page_fac_id = "data/fac_gum.json"
        bot.send_message(message.from_user.id, f"{get_questions(page_fac_id)}", parse_mode="Markdown")
        question_list_message = bot.send_message(message.from_user.id, f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                                           ,reply_markup=markup2, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, question_list_message.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_gum)

@bot.callback_query_handler(state = Back_fac.back_fac_man, func = lambda callback: True)
def back_fac_man(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'back':
        bot_back_fac_man_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _", reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_back_fac_man_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'ask_question':
        bot_go_fac_man_message = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_go_fac_man_message.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_man)
    elif message.data == 'support':
        get_chat_info()
        feedback_message = bot.send_message(message.from_user.id,
                                            f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=markup5, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.back_request)
    elif message.data == 'answer_1':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №1:* " + "\n\n" + answer[0], reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_man)
    elif message.data == 'answer_2':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №2:* " + "\n\n" + answer[1],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_man)
    elif message.data == 'answer_3':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №3:* " + "\n\n" + answer[2],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_man)
    elif message.data == 'rephrase':
        rephrase_mess = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, rephrase_mess.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_man)
    elif message.data == 'question_list':
        page_fac_id = 'data/fac_man.json'
        bot.send_message(message.from_user.id, f"{get_questions(page_fac_id)}", parse_mode="Markdown")
        question_list_message = bot.send_message(message.from_user.id, f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                                           ,reply_markup=markup2, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, question_list_message.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_man)


@bot.callback_query_handler(state = Back_fac.back_fac_law, func = lambda callback: True)
def back_fac_law(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'back':
        bot_back_fac_law_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _", reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_back_fac_law_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'ask_question':
        bot_go_fac_law_message = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_go_fac_law_message.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_law)
    elif message.data == 'support':
        get_chat_info()
        feedback_message = bot.send_message(message.from_user.id,
                                            f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=markup5, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.back_request)
    elif message.data == 'answer_1':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №1:* " + "\n\n" + answer[0],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_law)
    elif message.data == 'answer_2':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №2:* " + "\n\n" + answer[1],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_law)
    elif message.data == 'answer_3':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №3:* " + "\n\n" + answer[2],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_law)
    elif message.data == 'rephrase':
        rephrase_mess = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, rephrase_mess.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_law)
    elif message.data == 'question_list':
        page_fac_id = 'data/fac_law.json'
        bot.send_message(message.from_user.id, f"{get_questions(page_fac_id)}", parse_mode="Markdown")
        question_list_message = bot.send_message(message.from_user.id, f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                                           ,reply_markup=markup2, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, question_list_message.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_law)

@bot.callback_query_handler(state = Back_fac.back_fac_econ, func = lambda callback: True)
def back_fac_econ(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'back':
        bot_back_fac_econ_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _", reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_back_fac_econ_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'ask_question':
        bot_go_fac_econ_message = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_go_fac_econ_message.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_econ)
    elif message.data == 'support':
        get_chat_info()
        feedback_message = bot.send_message(message.from_user.id,
                                            f"*В данном отделе бота *" + f"_ты можешь отправить запрос в _" + f"*Комитет Качества Образования студсовета Вышки.*" + "\n\n" +
                                            f"*Это стоит делать*" + f"_ в случае конфликтной ситуации при учебном процессе, не типового вопроса, не соответствии коэффициентов накопа и экзамена ПУДУ и в т.п случаях._",
                                            reply_markup=markup5, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.back_request)
    elif message.data == 'answer_1':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №1:* " + "\n\n" + answer[0], reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_econ)
    elif message.data == 'answer_2':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №2:* " + "\n\n" + answer[1],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_econ)
    elif message.data == 'answer_3':
        question_answer = bot.send_message(message.from_user.id, f"*Ответ на вопрос №3:* " + "\n\n" + answer[2],
                                           reply_markup=markup3, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, question_answer.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_econ)
    elif message.data == 'rephrase':
        rephrase_mess = bot.send_message(message.from_user.id, f"_Напиши свой вопрос. _" + "\n\n" +
                                                 f"*Пример: *" + f"_Получить справку об обучении КНТ._", parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, rephrase_mess.message_id)
        bot.set_state(message.from_user.id, Faculties_types.fac_econ)
    elif message.data == 'question_list':
        page_fac_id = "data/fac_econ.json"
        bot.send_message(message.from_user.id, f"{get_questions(page_fac_id)}", parse_mode="Markdown")
        question_list_message = bot.send_message(message.from_user.id, f"*Вы хотите задать вопрос *" + f"_связанный с выбранным факультетом _"
                                         + f"*или обратиться *" + f"_Комитет качества образования?_"
                                           ,reply_markup=markup2, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, question_list_message.message_id)
        bot.set_state(message.from_user.id, Back_fac.back_fac_econ)

@bot.message_handler(state=Faculties_types.fac_it)
def fac_it(message):
    page_id_fac= 'fac_it.json'
    # log start
    current_data = datetime.date.today()
    current_time = datetime.datetime.now().time()
    print(str(message.from_user.id) + ": " + "(date: " + str(current_data) + ", time: " + str(
        current_time) + ")" + "\n" + "Message: " + message.text)
    # log end
    answer_bot_message = bot.send_message(message.from_user.id, f"{get_answer(message.text, page_id_fac)}", reply_markup=markup4, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, answer_bot_message.message_id)
    bot.set_state(message.from_user.id, Back_fac.back_fac_it)

@bot.message_handler(state=Faculties_types.fac_gum)
def fac_gum(message):
    page_id_fac = 'fac_gum.json'
    # log start
    current_data = datetime.date.today()
    current_time = datetime.datetime.now().time()
    print(str(message.from_user.id) + ": " + "(date: " + str(current_data) + ", time: " + str(
        current_time) + ")" + "\n" + "Message: " + message.text)
    # log end
    answer_bot_message = bot.send_message(message.from_user.id, f"{get_answer(message.text, page_id_fac)}", reply_markup=markup4, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, answer_bot_message.message_id)
    bot.set_state(message.from_user.id, Back_fac.back_fac_gum)

@bot.message_handler(state=Faculties_types.fac_man)
def fac_man(message):
    page_id_fac = 'fac_man.json'
    # log start
    current_data = datetime.date.today()
    current_time = datetime.datetime.now().time()
    print(str(message.from_user.id) + ": " + "(date: " + str(current_data) + ", time: " + str(
        current_time) + ")" + "\n" + "Message: " + message.text)
    # log end
    answer_bot_message = bot.send_message(message.from_user.id, f"{get_answer(message.text, page_id_fac)}", reply_markup=markup4, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, answer_bot_message.message_id)
    bot.set_state(message.from_user.id, Back_fac.back_fac_man)

@bot.message_handler(state=Faculties_types.fac_law)
def fac_law(message):
    page_id_fac = 'fac_law.json'
    # log start
    current_data = datetime.date.today()
    current_time = datetime.datetime.now().time()
    print(str(message.from_user.id) + ": " + "(date: " + str(current_data) + ", time: " + str(
        current_time) + ")" + "\n" + "Message: " + message.text)
    # log end
    answer_bot_message = bot.send_message(message.from_user.id, f"{get_answer(message.text, page_id_fac)}", reply_markup=markup4, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, answer_bot_message.message_id)
    bot.set_state(message.from_user.id, Back_fac.back_fac_law)

@bot.message_handler(state=Faculties_types.fac_econ)
def fac_econ(message):
    page_id_fac = 'fac_econ.json'
    # log start
    current_data = datetime.date.today()
    current_time = datetime.datetime.now().time()
    print(str(message.from_user.id) + ": " + "(date: " + str(current_data) + ", time: " + str(
        current_time) + ")" + "\n" + "Message: " + message.text)
    # log end
    answer_bot_message = bot.send_message(message.from_user.id, f"{get_answer(message.text, page_id_fac)}", reply_markup=markup4, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, answer_bot_message.message_id)
    bot.set_state(message.from_user.id, Back_fac.back_fac_econ)

@bot.message_handler(state=KKO_group.get_id)
def get_id(message):
    get_to_user_id(int(message.text))
    request_message = bot.send_message(chat_information[2], f"_Пришлите _" + f"*ответ на запрос*" + f"_ студента в формате одного сообщения._", parse_mode="Markdown")
    put_last_message_id(message.from_user.id, request_message.message_id)
    bot.set_state(message.from_user.id, KKO_group.check_answer, chat_information[2])

@bot.message_handler(state=KKO_group.check_answer)
def check_answer(message):
    bot.delete_message(chat_information[2], messages_id.get(message.from_user.id))
    ans_request_message(message.text)
    check_answer = bot.send_message(chat_information[2], f"_Ваш ответ на запрос: _" + "\n\n" + f"{message.text}" + '\n\n' + f"*ID студента: *" + "\n" + str(send_user_id),
                                    reply_markup = markup8, parse_mode="Markdown")
    put_last_message_id(message.from_user.id, check_answer.message_id)
    bot.set_state(message.from_user.id, KKO_group.status_answer, chat_information[2])

@bot.callback_query_handler(state=KKO_group.status_answer, func = lambda callback: True)
def status_answer(message):
    if message.data == 'send_answer':
        status_message = bot.send_message(chat_information[2], f"_Ваш ответ на запрос отправлен._", parse_mode="Markdown")
        bot.send_message(send_user_id, f"*Ответ на запрос от ККО: *" + "\n\n" + f"{ans_req_message}", reply_markup=markup7, parse_mode="Markdown")
        bot.set_state(send_user_id, KKO_group.feedback_answer)
    elif message.data == 'write_again':
        bot.delete_message(chat_information[2], messages_id.get(message.from_user.id))
        request_message = bot.send_message(chat_information[2], f"_Пришлите _" + f"*ответ на запрос*" + f"_ студента в формате одного сообщения._", parse_mode="Markdown")
        put_last_message_id(message.from_user.id, request_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.check_answer, chat_information[2])
    elif message.data == 'back':
        bot.delete_message(chat_information[2], messages_id.get(message.from_user.id))
        feedback_message = bot.send_message(chat_information[2], f"_Пришлите_" + f"* ID студента,*" + f"_ которому отвечаете._", parse_mode="Markdown")
        put_last_message_id(message.from_user.id, feedback_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.get_id, chat_information[2])

@bot.callback_query_handler(state=KKO_group.feedback_answer, func = lambda callback: True)
def feedback_answer(message):
    if message.data =='accepted':
        bot.send_message(message.from_user.id, f"_Рад тебе помочь!_" , parse_mode = "Markdown")
        bot_back_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _",
                                                    reply_markup=markup1, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, bot_back_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'not_accepted':
        bot.send_message(message.from_user.id, f"_Ты можешь обратиться к одному из сотрудников_"+ f"* ККО:*" + "\n\n" + chat_information[1], parse_mode = "Markdown")
        bot_back_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _",
                                            reply_markup=markup1, parse_mode="Markdown")
        put_last_message_id(message.from_user.id, bot_back_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)


@bot.callback_query_handler(state=KKO_group.back_request, func = lambda callback: True)
def back_request_message(message):
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    if message.data == 'write_request':
        explain_message = bot.send_message(message.from_user.id, f"_Напиши свой запрос: _" + "\n\n" + f"_В твоем запросе _" + f"*ты должен указать*" + f"_ свое ФИО, факультет, учебную группу._"
                                                 , parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, explain_message.message_id)
        bot.set_state(message.from_user.id, KKO_group.correct_request)
    elif message.data == 'back':
        bot_first_message = bot.send_message(message.from_user.id, f"_Выбери свой факультет: _", reply_markup=markup1, parse_mode = "Markdown")
        put_last_message_id(message.from_user.id, bot_first_message.message_id)
        bot.set_state(message.from_user.id, MainStates.problem_types)
    elif message.data == 'send_request':
        bot.send_message(chat_information[2], f"*Запрос от студента: *" + "\n\n" + f"{request_message}" + "\n\n" + f"*ID студента: *" + "\n" + str(message.from_user.id), parse_mode="Markdown")
        bot.send_message(message.from_user.id, f"*Ваш запрос *" + f"_направлен _" + f"*в ККО.*" + "\n\n" +
                         f"_Максимальное время ответа - _" + f"*2 дня.*" , parse_mode="Markdown")


@bot.message_handler(state=KKO_group.correct_request)
def request_check(message):
    put_request_message(f"{message.text}")
    # log start
    current_data = datetime.date.today()
    current_time = datetime.datetime.now().time()
    print(str(message.from_user.id) + ": " + "(date: " + str(current_data) + ", time: " + str(
        current_time) + ")" + "\n" + "Message: " + message.text)
    # log end
    bot.delete_message(message.from_user.id, messages_id.get(message.from_user.id))
    request_message = bot.send_message(message.from_user.id, f"_Ваш запрос выглядит так: _" + "\n\n" + f"{message.text}" + "\n\n" +
                                       f"*Проверьте, написали ли вы:*" + f"_ учебную группу, факультет, ФИО._" , reply_markup=markup6, parse_mode = "Markdown")
    put_last_message_id(message.from_user.id, request_message.message_id)
    bot.set_state(message.from_user.id, KKO_group.back_request)

#Answer to request
ans_req_message = ""
def ans_request_message(ans_request):
    global ans_req_message
    ans_req_message = ans_request

#Request for KKO
request_message = ""
def put_request_message(request):
    global request_message
    request_message = request

#Get to user id
send_user_id = 0
def get_to_user_id(user_id):
    global send_user_id
    send_user_id = user_id

#Get chat id
chat_information = ['', '', 0]
def get_chat_id(storage_chat):
    global chat_information
    chat_information = storage_chat

#Last answer for user
answer = ['', '', '']
def put_answer(storage):
    global answer
    answer = storage

#Put the new sentence
sentence = ['', '', '']
def put_sentence(index, storage):
    global sentence
    sentence[index] = storage

#Put file name
file_name = ""
def put_file_name(data_file):
    global file_name
    file_name = data_file


#Messages id
messages_id = {}
def put_last_message_id(user_id, message_id):
    global messages_id
    messages_id[user_id] = message_id

#Загрузка данных
def load_data(data_file):
    try:
        with open(data_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []  # Если файл не существует, возвращаем пустой список
#Сохранение данных
def save_data(data_file, data):
    with open(data_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

#Добавление данных
def add_data(file_name, col1, col2):
    data = load_data(file_name)
    data.append([col1, col2])
    save_data(file_name, data)
#Удаление данных

def remove_data(file_name, index):
    data = load_data(file_name)
    if 0 <= index < len(data):
        removed = data.pop(index)
        save_data(file_name, data)
        print(f"Удалены данные: {removed}")
    else:
        print("Некорректный индекс!")

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)