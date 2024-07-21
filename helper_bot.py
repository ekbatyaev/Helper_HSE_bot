# import telebot
# import json
# import requests
# from datetime import datetime, timezone
# from telebot import types, TeleBot
# from notion_client import Client
# from pprint import pprint
# from telebot import custom_filters
# from telebot.handler_backends import State, StatesGroup
# from telebot.storage import StateMemoryStorage
# notion_token = "secret_N8zfGUMB144nM1TMojVYmSQtyMt2A5pu6RgyCmlcNL3"
# notion_page_id = "e4600d549cf444049fc51bdd438ad0aa"
# notion_database_id = notion_page_id
#
# state_storage = StateMemoryStorage()
# bot = telebot.TeleBot('7244080071:AAFOVCYOk1ImVfKvMkFn8AJTkN7aZkfFMkU', state_storage=state_storage)
#
# def write_dict_to_file_as_json(content, file_name):
#     content_as_json_str = json.dumps(content)
#
#     with open(file_name, 'w') as f:
#         f.write(content_as_json_str)
#
#
# def read_text(client, page_id):
#     response = client.blocks.children.list(block_id=page_id)
#     return response['results']
#
#
# def safe_get(data, dot_chained_keys):
#     '''
#         {'a': {'b': [{'c': 1}]}}
#         safe_get(data, 'a.b.0.c') -> 1
#     '''
#     keys = dot_chained_keys.split('.')
#     for key in keys:
#         try:
#             if isinstance(data, list):
#                 data = data[int(key)]
#             else:
#                 data = data[key]
#         except (KeyError, TypeError, IndexError):
#             return None
#     return data
#
#
# def main():
#     client = Client(auth=notion_token)
#
#     db_info = client.databases.retrieve(database_id=notion_database_id)
#
#     write_dict_to_file_as_json(db_info, 'db_info.json')
#
#     db_rows = client.databases.query(database_id=notion_database_id)
#
#     write_dict_to_file_as_json(db_rows, 'db_rows.json')
#
#     simple_rows = []
#
#     for row in db_rows['results']:
#
#         fac_it = safe_get(row, 'properties.Faculty_iT - questions.title.0.plain_text')
#         answer = safe_get(row, 'properties.Answer.plain_text')
#         type_of_question = safe_get(row, 'properties.Event.plain_text')
#
#         simple_rows.append({
#             'Faculty': fac_it,
#             'Answer': answer,
#             'Type of question': type_of_question
#         })
#
#     write_dict_to_file_as_json(simple_rows, 'simple_rows.json')
#
#
# if __name__ == '__main__':
#     main()
# #Classes of States
# class MainStates (StatesGroup):
#     start_state = State()
#     problem_types = State()
#
# class Back_fac (StatesGroup):
#     back_fac_it = State()
#     back_fac_gum = State()
#     back_fac_econ = State()
#     back_fac_law = State()
#     back_fac_man = State()
#
# class Faculties_types(StatesGroup):
#     fac_it = State()
#     fac_gum = State()
#     fac_econ = State()
#     fac_law = State()
#     fac_man = State()
#
# # KeyBoard
# markup = types.InlineKeyboardMarkup()
# item1 = types.InlineKeyboardButton('Начать работу', callback_data = 'Начать работу')
# markup.add(item1)
#
# markup1 = types.InlineKeyboardMarkup(row_width = 1)
# item1 = types.InlineKeyboardButton('Факультет информатики, математики и компьютерных наук', callback_data='choice_1')
# item2 = types.InlineKeyboardButton('Факультет гуманитарных наук', callback_data='choice_2')
# item3 = types.InlineKeyboardButton('Факультет менеджмента', callback_data= 'choice_3')
# item4 = types.InlineKeyboardButton('Факультет права', callback_data='choice_4')
# item5 = types.InlineKeyboardButton('Факультет экономики', callback_data='choice_5')
# markup1.add(item1, item2, item3, item4, item5)
#
# markup2 = types.InlineKeyboardMarkup(row_width = 1)
# item1 = types.InlineKeyboardButton('Задать вопрос', callback_data='ask_question')
# item2 = types.InlineKeyboardButton('Назад', callback_data= 'back')
# markup2.add(item1, item2)
#
#
# @bot.message_handler(commands=['start'])
# def start_message(message):
#
#
#     bot_start_message = bot.send_message(message.from_user.id,"Привет, вышкинец)\n\n"
#                      "Я бот, в котором ты можешь получить ответ на все интересующие тебя вопросы по поводу обучения в Вышке.\n\n"
#                      "А также получить оперативный ответ от представителей ККО студсовета Вышки. "
#                      ,reply_markup=markup)
#     handle_message(bot_start_message.message_id)
#     bot.set_state(message.from_user.id, MainStates.start_state, message.chat.id)
#
#
#
# @bot.callback_query_handler(state=MainStates.start_state, func = lambda callback: True)
# def first_message(message):
#     bot.delete_message(message.from_user.id, last_message_id)
#     if message.data == 'Начать работу':
#         bot_first_message = bot.send_message(message.from_user.id, "Выбери свой факультет", reply_markup=markup1)
#         handle_message(bot_first_message.message_id)
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#
#
# @bot.callback_query_handler(state=MainStates.problem_types, func = lambda callback: True)
# def problem_types(message):
#     bot.delete_message(message.from_user.id, last_message_id)
#     bot_problem_types = bot.send_message(message.from_user.id, 'Вы хотите задать вопрос связанный с выбранным факультетом?\n'
#                                            'Пример: Время работы учебного офиса.', reply_markup=markup2)
#     handle_message(bot_problem_types.message_id)
#     if message.data == 'choice_1':
#         bot.set_state(message.from_user.id, Back_fac.back_fac_it)
#     elif message.data == 'choice_2':
#         bot.set_state(message.from_user.id, Back_fac.back_fac_gum)
#     elif message.data == "choice_3":
#         bot.set_state(message.from_user.id, Back_fac.back_fac_man)
#     elif message.data == "choice_4":
#         bot.set_state(message.from_user.id, Back_fac.back_fac_law)
#     elif message.data == "choice_5":
#         bot.set_state(message.from_user.id, Back_fac.back_fac_econ)
#     else:
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#
# @bot.callback_query_handler(state = Back_fac.back_fac_it, func = lambda callback: True)
# def back_fac_it(message):
#     if message.data == 'back':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_back_fac_it_message = bot.send_message(message.from_user.id, "Выбери свой факультет", reply_markup=markup1)
#         handle_message(bot_back_fac_it_message.message_id)
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#     elif message.data == 'ask_question':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_go_fac_it_message = bot.send_message(message.from_user.id, "Ваш вопрос:\n")
#         handle_message(bot_go_fac_it_message.message_id)
#         bot.set_state(message.from_user.id, Faculties_types.fac_it)
#
# @bot.callback_query_handler(state = Back_fac.back_fac_gum, func = lambda callback: True)
# def back_fac_gum(message):
#     if message.data == 'back':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_back_fac_gum_message = bot.send_message(message.from_user.id, "Выбери свой факультет", reply_markup=markup1)
#         handle_message(bot_back_fac_gum_message.message_id)
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#     elif message.data == 'ask_question':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_go_fac_gum_message = bot.send_message(message.from_user.id, "Ваш вопрос:\n")
#         handle_message(bot_go_fac_gum_message.message_id)
#         bot.set_state(message.from_user.id, Faculties_types.fac_gum)
#
# @bot.callback_query_handler(state = Back_fac.back_fac_man, func = lambda callback: True)
# def back_fac_man(message):
#     if message.data == 'back':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_back_fac_man_message = bot.send_message(message.from_user.id, "Выбери свой факультет", reply_markup=markup1)
#         handle_message(bot_back_fac_man_message.message_id)
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#     elif message.data == 'ask_question':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_go_fac_man_message = bot.send_message(message.from_user.id, "Ваш вопрос:\n")
#         handle_message(bot_go_fac_man_message.message_id)
#         bot.set_state(message.from_user.id, Faculties_types.fac_man)
#
# @bot.callback_query_handler(state = Back_fac.back_fac_law, func = lambda callback: True)
# def back_fac_law(message):
#     if message.data == 'back':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_back_fac_law_message = bot.send_message(message.from_user.id, "Выбери свой факультет", reply_markup=markup1)
#         handle_message(bot_back_fac_law_message.message_id)
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#     elif message.data == 'ask_question':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_go_fac_law_message = bot.send_message(message.from_user.id, "Ваш вопрос:\n")
#         handle_message(bot_go_fac_law_message.message_id)
#         bot.set_state(message.from_user.id, Faculties_types.fac_law)
#
# @bot.callback_query_handler(state = Back_fac.back_fac_econ, func = lambda callback: True)
# def back_fac_econ(message):
#     if message.data == 'back':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_back_fac_econ_message = bot.send_message(message.from_user.id, "Выбери свой факультет", reply_markup=markup1)
#         handle_message(bot_back_fac_econ_message.message_id)
#         bot.set_state(message.from_user.id, MainStates.problem_types)
#     elif message.data == 'ask_question':
#         bot.delete_message(message.from_user.id, last_message_id)
#         bot_go_fac_econ_message = bot.send_message(message.from_user.id, "Ваш вопрос:\n")
#         handle_message(bot_go_fac_econ_message.message_id)
#         bot.set_state(message.from_user.id, Faculties_types.fac_econ)
#
# @bot.message_handler(state=Faculties_types.fac_it)
# def fac_it(message):
#     bot.send_message(message.from_user.id, 'Ваш вопрос получен')
#
# @bot.message_handler(state=Faculties_types.fac_gum)
# def fac_gum(message):
#     bot.send_message(message.from_user.id, 'Ваш вопрос получен')
#
# @bot.message_handler(state=Faculties_types.fac_man)
# def fac_man(message):
#     bot.send_message(message.from_user.id, 'Ваш вопрос получен')
#
# @bot.message_handler(state=Faculties_types.fac_law)
# def fac_law(message):
#     bot.send_message(message.from_user.id, 'Ваш вопрос получен')
#
# @bot.message_handler(state=Faculties_types.fac_econ)
# def fac_econ(message):
#     bot.send_message(message.from_user.id, 'Ваш вопрос получен')
#
# #Last message bot id
# last_message_id = 0
# def handle_message(update):
#     global last_message_id
#     last_message_id = update
#
#
# bot.add_custom_filter(custom_filters.StateFilter(bot))
# bot.infinity_polling(skip_pending=True)