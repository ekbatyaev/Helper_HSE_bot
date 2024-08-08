import re


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


# Пример использования
pattern = "получить справку об обучении в ВУЦ"
texts = [
    "Справка для военкомата",
    "Получить справку об обучении для военкомата",
    "Что такое майнор?",
    "Информация о поступлении в Военный Учебный Центр (ВУЦ)"
]

matches = get_matches(pattern, "Информация о поступлении в Военный Учебный Центр (ВУЦ)")
print(matches)
# for match in matches:
#     print(f"Совпадений: {match[0]}, Предложение: '{match[1]}'")