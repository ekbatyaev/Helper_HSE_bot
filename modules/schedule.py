import requests
import os
import pandas as pd
import asyncio
async def send_schedule():
    # Ссылка на Google Sheets с экспортом в Excel
    url = 'https://docs.google.com/spreadsheets/d/1v2XrEcod_Mlo97h97TRpcgSlu1RoRMqh7vMWUpUilrc/export?format=xlsx'
    #url = 'https://docs.google.com/spreadsheets/d/1LTtSol8D7vXeYGZVmE7yGDSYE4jV3MKY7IustIcY8Jk/export?format=xlsx'

    # Папка для сохранения файла
    folder_path = '../list_of_schedules'
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, 'table.xlsx')

    # Загрузка файла
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print('Файл успешно загружен!')
    else:
        print(f'Произошла ошибка при загрузке файла: {response.status_code}')

    # Проверка существования файла и чтение данных
    if os.path.exists(file_path):
        try:
            # Настройка pandas для отображения всех данных
            pd.set_option('display.max_rows', None)  # Показать все строки
            pd.set_option('display.max_columns', None)  # Показать все столбцы
            pd.set_option('display.expand_frame_repr', False)  # Отключить перенос строк

            # Открытие Excel-файла
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')

            # Список всех листов
            print('Листы в файле:', excel_file.sheet_names)

            # Чтение второго листа
            second_sheet = pd.read_excel(file_path, sheet_name=2, engine='openpyxl')  # Индекс 1 = второй лист
            print('Второй лист успешно прочитан!')
            second_sheet = second_sheet.fillna("")

            # Вывод всех данных второго листа
            print(second_sheet)
            time = "08:00-09:20+09:30-10:50+11:10-12:30+13:00-14:20+14:40-16:00+16:20-17:40+18:10-19:30+19:40-21:00"
            time = time.split("+")
            weekdays = "Понедельник+Вторник+Среда+Четверг+Пятница+Суббота"
            weekdays = weekdays.split("+")
            # Пример доступа к отдельным значениям
            print("\nДоступ к отдельным значениям:")
            print("Значение в первой строке и первом столбце:", second_sheet.iloc[1])  # По индексу
            #column_data = second_sheet.loc[:, "Имя_столбца"]  # Доступ к столбцу по имени
            #print("Значение из столбца 'Имя_столбца':", column_data)
            column_data_lessons = second_sheet.iloc[9:59, 4]# Доступ к первому столбцу
            column_data_lessons = column_data_lessons.to_list()
            print(column_data_lessons)
            column_data_time = second_sheet.iloc[11:59, 2]  # Доступ к первому столбцу
            column_data_time = column_data_time.to_list()
            print(column_data_time)
            column_data_rooms = second_sheet.iloc[11:59, 5]  # Доступ к первому столбцу
            column_data_rooms = column_data_rooms.to_list()
            print(column_data_rooms)
            #print("Группа: " + column_data_lessons[0] + "\n")
            index = 0
            schedule = ""
            column_data_lessons = column_data_lessons[2:]
            for weekday in weekdays:
                schedule += u"📚" + weekday + u"📚" + "\n\n"
                check = 0
                check += sum(len(column_data_lessons[index + p]) for p in range (8))
                print(check)
                if not check:
                    schedule += "*В этот день пары нет*" + "\n\n"
                #check += sum(column_data_lessons[index + p] for p in range(8))
                # if column_data_lessons[index - 1] == "Занятия по дисциплинам дополнительного профиля MINOR":
                if column_data_time[index - 1] == 0:
                    schedule += "*" + column_data_lessons[index] + "*     _"  + column_data_rooms[index] + "_" "\n\n"
                    index+=4
                    schedule += "\n\n"
                    continue
                for i in range(8):
                    if column_data_lessons[index + i]  == '':
                        continue
                    schedule += column_data_time[index + i] + ": " + "*" + column_data_lessons[index + i] + "*     _" + column_data_rooms[index + i] + "_" + "\n\n"
                schedule += "\n\n"
                index+=9

            return schedule








        #print("Значение в первой строке и столбце 'Название':", second_sheet.at[10, 'БАКАЛАВРИАТ - 2 курс, 3 модуль (09.01. - 24.03.)'])  # По названию столбца

        except Exception as e:
            print('Ошибка при чтении файла:', e)
    else:
        print('Файл не найден после загрузки.')
