import os
import torch
import requests
import json
import numpy as np
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import cosine_similarity
from typing import Dict, Any
import logging

# Логирование состояний
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Конфигурация
MODEL_NAME = "intfloat/multilingual-e5-large"
API_TOKEN = os.getenv("API_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# Глобальные переменные для модели и токенизатора
tokenizer = None
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global tokenizer, model

    # Загрузка модели при старте
    logger.info("Loading tokenizer and model...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME)
        logger.info("Model and tokenizer loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

    yield

    # Очистка ресурсов при остановке (если требуется)
    logger.info("Shutting down...")


app = FastAPI(title="HSE Chatbot Model API", lifespan=lifespan)


class SearchRequest(BaseModel):
    question: str
    faculty_name: str

def verify_token(token: str):
    """Проверка авторизационного токена"""
    if token != API_TOKEN:
        logger.warning(f"Unauthorized access attempt with token: {token}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return token


async def get_pages(page_id: str, headers: Dict[str, str], num_pages: int = None) -> list:
    """Получение страниц из Notion API"""
    url = f"https://api.notion.com/v1/databases/{page_id}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    try:
        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data["results"]
        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            results.extend(data["results"])

        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API request failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Notion API service unavailable"
        )


async def extract_rich_text(rich_text_array: list) -> str:
    """Форматирование текста из Notion"""
    content = ""
    for item in rich_text_array:
        text_content = item.get("text", {}).get("content", "")
        annotations = item.get("annotations", {})

        if annotations.get("bold"):
            text_content = f"*{text_content}*"
        if annotations.get("italic"):
            text_content = f"_{text_content}_"
        if annotations.get("underline"):
            text_content = f"~{text_content}~"

        content += text_content
    return content


async def parse_questions(fac_page_id: str, headers: Dict[str, str], common_questions_page_id: str) -> list:
    """Парсинг вопросов из Notion"""
    information = []
    all_len = 0

    for page_id in [common_questions_page_id, fac_page_id]:
        try:
            pages = await get_pages(page_id, headers)
            for page in pages:
                props = page["properties"]
                question = "".join([
                    part.get("text", {}).get("content", "")
                    for part in props.get("Вопрос", {}).get("title", [])
                ])
                answer = props.get("Ответ", {}).get("rich_text", [])
                formatted_answer = await extract_rich_text(answer)
                all_len += len(question) + len(formatted_answer)
                information.append([0, question, formatted_answer])

        except Exception as e:
            logger.error(f"Error parsing questions for page {page_id}: {str(e)}")
            continue

    return [information, all_len]


async def get_embeddings(texts: list) -> torch.Tensor:
    """Получение эмбеддингов для текста"""
    try:
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state[:, 0, :]

    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Embedding generation error"
        )


async def load_embeddings(faculty_name: str) -> list:
    """Загрузка или создание эмбеддингов"""
    file_path = Path(__file__).parent / "embeddings"
    file_path.mkdir(exist_ok=True)

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    try:
        data = await load_data(file_path / "emb_info.json")
        common_questions_page_id = data.get("common_questions", {}).get("page_id")

        information, symbols_count = await parse_questions(
            data[faculty_name]["page_id"], headers, common_questions_page_id
        )

        emb_file = file_path / f"emb_{faculty_name}.npy"

        if data[faculty_name].get("symbols_count") != symbols_count or not emb_file.exists():
            questions = [cell[1] for cell in information]
            questions_embeddings = await get_embeddings(questions)
            data[faculty_name]["symbols_count"] = symbols_count

            np.save(emb_file, questions_embeddings.numpy())
            await save_data(file_path / "emb_info.json", data)
        else:
            questions_embeddings = torch.from_numpy(np.load(emb_file))

        for i, emb in enumerate(questions_embeddings):
            information[i][0] = emb

        return information

    except Exception as e:
        logger.error(f"Error loading embeddings for {faculty_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load embeddings: {str(e)}"
        )


async def load_data(data_file: Path) -> Dict:
    """Загрузка данных из JSON файла"""
    try:
        with open(data_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


async def save_data(data_file: Path, data: Dict) -> None:
    """Сохранение данных в JSON файл"""
    try:
        with open(data_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")


@app.post("/search")
async def search_api(request: SearchRequest, token: str = Depends(verify_token)):
    """Поиск ответов на вопросы"""
    try:
        logger.info(f"Processing question: {request.question[:50]}... for {request.faculty_name}")

        pre_work_info = await load_embeddings(request.faculty_name)
        if not pre_work_info:
            return {
                "question": request.question,
                "error": "No data available",
                "answer": "Данные для этого факультета не найдены"
            }

        user_question_emb = await get_embeddings([request.question])
        database_questions_embed = torch.stack([torch.as_tensor(cell[0]) for cell in pre_work_info])

        similarities = cosine_similarity(
            user_question_emb.unsqueeze(1),
            database_questions_embed.unsqueeze(0),
            dim=-1
        )

        if similarities.numel() == 0:
            logger.warning("No similarities found")
            return {
                "question": request.question,
                "error": "No similarities found",
                "answer": "Я не смог найти ответ на твой вопрос 🙁"
            }

        best_match_idx = similarities.argmax().item()
        if best_match_idx >= len(pre_work_info):
            logger.error(f"Index {best_match_idx} out of range for {len(pre_work_info)} items")
            return {
                "question": request.question,
                "error": "Index out of range",
                "answer": "Я не смог найти ответ на твой вопрос 🙁"
            }

        best_match = pre_work_info[best_match_idx][1]
        best_score = similarities.flatten()[best_match_idx].item()
        context = pre_work_info[best_match_idx][2]

        print(f"answer: {request.question} {best_score} {best_match}")

        # Разбиваем контекст на части, если он слишком большой
        max_context_length = 512  # Максимальная длина контекста для сравнения
        context_parts = [context[i:i + max_context_length] for i in range(0, len(context), max_context_length)]

        # Получаем эмбеддинги для каждой части контекста
        context_embs = []
        for part in context_parts:
            emb = await get_embeddings(part)
            context_embs.append(emb)

        # Вычисляем сходство с каждой частью контекста
        max_context_similarity = 0
        for emb in context_embs:
            similarities_context = cosine_similarity(
                user_question_emb.unsqueeze(1), emb.unsqueeze(0), dim=-1
            )
            current_sim = similarities_context.item()
            if current_sim > max_context_similarity:
                max_context_similarity = current_sim

        print(f"Max context similarity: {max_context_similarity}")

        # Проверяем оба условия: сходство с вопросом и с контекстом
        if best_score < 0.85 or (best_score < 0.89 and max_context_similarity < 0.85):
            return {
                "question": request.question,
                "score": best_score,
                "best_match": best_match,
                "answer": "Я не смог найти точный ответ на твой вопрос 🙁"
            }
        return {
            "question": request.question,
            "score": best_score,
            "best_match": best_match,
            "answer": pre_work_info[best_match_idx][2]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "model_loaded": model is not None,
        "tokenizer_loaded": tokenizer is not None
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,
        access_log=False,
        lifespan="on"
    )