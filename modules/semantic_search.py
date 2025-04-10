import asyncio
import os

import torch
import requests
import json
import numpy as np
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import cosine_similarity
from tokens_file import notion_token
from pathlib import Path


TOKEN = notion_token
HEADERS = {
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}
MODEL_NAME= "intfloat/multilingual-e5-large"

async def get_pages(page_id, num_pages=None):
    url = f"https://api.notion.com/v1/databases/{page_id}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages
    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=HEADERS)
    data = response.json()
    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        response = requests.post(url, json=payload, headers=HEADERS)
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

async def parse_questions(fac_page_id):
    information = []
    all_len = 0
    for page_id in [common_questions_page_id, fac_page_id]:
        pages = await get_pages(page_id)
        for page in pages:
            props = page["properties"]
            question = "".join([part.get("text", {}).get("content", "") for part in props.get("Вопрос", {}).get("title", [])])
            answer = props.get("Ответ", {}).get("rich_text", [])
            formatted_answer = await extract_rich_text(answer)
            all_len+=len(question) + len(formatted_answer)
            information.append([0, question, formatted_answer])
    return [information, all_len]


async def get_embeddings(texts):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :]  # Берем CLS-токен

async def load_embeddings(faculty_name):
    file_path = f"{Path(__file__).parent.parent}" + "/embeddings"
    data = await load_data(f"{file_path}/emb_info.json")
    information, symbols_count = await parse_questions(data[faculty_name]["page_id"])
    if data[faculty_name]["symbols_count"] != symbols_count:
        questions = [cell[1] for cell in information]
        questions_embeddings = await get_embeddings(questions)
        data[faculty_name]["symbols_count"] = symbols_count
        np.save(f"{file_path}/emb_{faculty_name}.npy", questions_embeddings)
        await save_data(f"{file_path}/emb_info.json", data)
    elif os.path.exists(f"{file_path}/emb_{faculty_name}.npy"):
        questions_embeddings = np.load(f"{file_path}/emb_{faculty_name}.npy")
    else:
        questions = [cell[1] for cell in information]
        questions_embeddings = await get_embeddings(questions)
        np.save(f"{file_path}/emb_{faculty_name}.npy", questions_embeddings)
    for i, emb in enumerate(questions_embeddings):
        information[i][0] = emb
    return information

async def search(user_question, faculty_name):
    pre_work_info = await load_embeddings(faculty_name)
    user_question_emb = await get_embeddings(user_question)
    database_questions_embed = torch.stack([torch.as_tensor(cell[0]) for cell in pre_work_info])
    similarities = cosine_similarity(
        user_question_emb.unsqueeze(1), database_questions_embed.unsqueeze(0), dim=-1
    )
    if similarities.numel() == 0:
        raise ValueError("Ошибка: similarities пустой!")
    best_match_idx = similarities.argmax().item()  # Индекс наибольшего сходства
    if best_match_idx >= len(pre_work_info):
        raise IndexError(f"Ошибка: best_match_idx ({best_match_idx}) выходит за границы {len(pre_work_info)}")

    best_match = pre_work_info[best_match_idx][1]
    best_score = similarities.flatten()[best_match_idx].item()  # Исправлено для корректного доступа
    print("answer: " + str(user_question) + " " + str(best_score) + " " + str(best_match))
    if best_score < 0.85:
        answer = "Я не смог найти ответ на твой вопрос 🙁"
        return [user_question, best_score, best_match, answer]
    return [user_question, best_score, best_match, pre_work_info[best_match_idx][2]]

#Загрузка данных из файла

async def load_data(data_file):
    try:
        with open(data_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []  # Если файл не существует, возвращаем пустой список

#Загрузка страницы общих вопросов
common_questions_page_id = asyncio.run(load_data(f"{Path(__file__).parent.parent}" + "/embeddings/emb_info.json")).get("common_questions").get("page_id")

#Сохранение данных

async def save_data(data_file, data):
    with open(data_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    asyncio.run(search("Что такое маголего?", "fac_it"))

