import asyncio

import torch
import requests
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import cosine_similarity
from tokens_file import notion_token

async def parse_questions():
    token = notion_token
    page_id = "ec48b9dacec340808876fbaf0947d4e6"
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
        formatted_answer = await extract_rich_text(answer)
        information.append([0, question, formatted_answer])
    return information


async def get_embeddings(texts):
    model_name = "intfloat/multilingual-e5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :]  # Берем CLS-токен

async def load_embeddings():
    information = await parse_questions()
    # Загружаем токенизатор и модель

    questions = []
    # Функция для преобразования текста в эмбеддинги

    for cell in information:
        questions.append(cell[1])

    # Преобразуем все вопросы в эмбеддинги
    questions_embeddings = await get_embeddings(questions)

    print(questions_embeddings)

    for i in range (len(information)):
        information[i][0] = questions_embeddings[i]

    return information

    # # Вычисляем косинусное сходство между каждым вопросом и пользовательскими вопросами
    # similarities = cosine_similarity(
    #     question_embeddings.unsqueeze(1), user_question_embeddings.unsqueeze(0), dim=-1
    # )

    # Находим самый похожий пользовательский вопрос для каждого вопроса
    # results = []
    # for i in range(len(questions)):
    #     best_match_idx = torch.argmax(similarities[i]).item()
    #     best_score = similarities[i][best_match_idx].item()
    #     best_match = user_questions[best_match_idx]
    #     results.append([questions[i], best_score, best_match])

async def search(user_question):
    work_info = pre_work_info
    # Преобразуем вопрос пользователя в эмбеддинг
    user_question_emb = await get_embeddings(user_question)
    model_name = "intfloat/multilingual-e5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    database_questions_embed = []
    for cell in pre_work_info:
        database_questions_embed.append(cell[0])
    print(database_questions_embed)
    database_questions_embed = torch.stack(database_questions_embed)
    # Вычисляем косинусное сходство между каждым вопросом и пользовательскими вопросами
    similarities = cosine_similarity(
        user_question_emb.unsqueeze(1), database_questions_embed.unsqueeze(0), dim=-1
    )

    #Находим самый похожий пользовательский вопрос для каждого вопроса

    # Проверяем размерность similarities
    print("similarities shape:", similarities.shape)
    print("similarities:", similarities)

    if similarities.numel() == 0:
        raise ValueError("Ошибка: similarities пустой!")

    best_match_idx = similarities.argmax().item()  # Индекс наибольшего сходства

    if best_match_idx >= len(work_info):
        raise IndexError(f"Ошибка: best_match_idx ({best_match_idx}) выходит за границы {len(work_info)}")

    best_match = work_info[best_match_idx][1]
    best_score = similarities.flatten()[best_match_idx].item()  # Исправлено для корректного доступа

    print("answer: "  + str(user_question) + str(best_score) + str(best_match))


if __name__ == '__main__':
    global pre_work_info
    pre_work_info = asyncio.run(load_embeddings())
    print(asyncio.run(search("Smart lms")))
    #print(pre_work_info)
