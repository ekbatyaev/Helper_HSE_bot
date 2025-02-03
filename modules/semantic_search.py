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
        formatted_answer = extract_rich_text(answer)
        information.append([0, question, formatted_answer])
    return information

async def load_embeddings():
    information = parse_questions()
    # Загружаем токенизатор и модель
    model_name = "intfloat/multilingual-e5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    # Функция для преобразования текста в эмбеддинги
    def get_embeddings(texts):
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state[:, 0, :]  # Берем CLS-токен

    # Преобразуем все вопросы в эмбеддинги
    question_embeddings = get_embeddings(questions[0])
    user_question_embeddings = get_embeddings(user_questions)

    # Вычисляем косинусное сходство между каждым вопросом и пользовательскими вопросами
    similarities = cosine_similarity(
        question_embeddings.unsqueeze(1), user_question_embeddings.unsqueeze(0), dim=-1
    )

    # Находим самый похожий пользовательский вопрос для каждого вопроса
    results = []
    for i in range(len(questions)):
        best_match_idx = torch.argmax(similarities[i]).item()
        best_score = similarities[i][best_match_idx].item()
        best_match = user_questions[best_match_idx]
        results.append([questions[i], best_score, best_match])

    # Выводим результаты
    for result in results:
        print(f"Вопрос: {result[0]}")
        print(f"Лучший матч: {result[2]}")
        print(f"Схожесть: {result[1]:.4f}")
        print("-" * 50)

    for result in results:
        print(result[0])

    print("\n\n")
    for result in results:
        print(f"{result[1]:.5f}")

    print("\n\n")
    for result in results:
        print(result[2])
