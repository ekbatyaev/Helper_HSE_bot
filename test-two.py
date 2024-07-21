import requests

token = "secret_N8zfGUMB144nM1TMojVYmSQtyMt2A5pu6RgyCmlcNL3"
#page_id = "627a3821e4db4c92a27bb7950f9e714b"
page_id = "ec48b9dacec340808876fbaf0947d4e6"
headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}
DATABASE_ID = page_id
def get_pages(num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    # Comment this out to dump all data to a file
    # import json
    # with open('db.json', 'w', encoding='utf8') as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

pages = get_pages()
information = []

for page in pages:

    page_id = page["id"]
    props = page["properties"]
    # question = props["Вопросы"]["title"][0]["text"]["content"]
    # answer = props["Ответы"]["rich_text"][0]["text"]["content"]
    # type_question = props["Тип вопроса"]["Multi-Select"][0]["text"]["content"]
    question = props.get("Вопросы", {}).get("title",  [{}])[0].get("text", {}).get("content", "")
    answer = props.get("Ответы", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
    information.append([0, question, answer])
    #type_question = props.get("Тип вопроса", {}).get("multi_select", [{}])[0].get("name", "")

    #print(question, answer)
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


# Использования
pattern = "tремя работы учебного офиса"
for i in range(0, len(information)):
    changes_needed = minimum_changes(information[i][1], pattern)
    information[i][0] = changes_needed
information.sort()
message_for_user ='Найденные ответы:\n'
for i in range(0, 4):
    message_for_user+=information[i][1] +'\n'
    message_for_user+="Ответ: " + information[i][2]+'\n'

print(message_for_user)