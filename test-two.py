def levenshtein_distance(pattern, text):
    n, m = len(pattern), len(text)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if pattern[i - 1] == text[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[n][m]

def modified_levenshtein_distance(pattern, text):
    base_distance = levenshtein_distance(pattern, text)
    max_match_length = 0

    # Найдем длину максимальной совпадающей подстроки
    n, m = len(pattern), len(text)
    for i in range(n):
        for j in range(m):
            length = 0
            while i + length < n and j + length < m and pattern[i + length] == text[j + length]:
                length += 1
            max_match_length = max(max_match_length, length)

    # Чем больше совпадающая подстрока, тем меньше итоговое расстояние
    adjustment = max_match_length

    # Длинные совпадающие подстроки уменьшают итоговое расстояние
    return base_distance - adjustment

# Примеры использования
pattern1 = "Получить справку об обучении для военкомата"
texts1 = ["военкомат", "Что такое майнор", "Что такое СОП", "Что такое Куд?"]

pattern2 = "Лишение скидки на обучение"
texts2 = ["лишение скидки", "Где узнать свои перцентиль, рейтинг, среднюю оценку (GPA), курсы, а также расписание?", "Какие экзамены есть по английскому языку?"]

# Вычислим расстояния для первого примера
distances1 = {text: modified_levenshtein_distance(pattern1, text) for text in texts1}
sorted_texts1 = sorted(distances1, key=distances1.get)

print("Пример №1:")
for text in sorted_texts1:
    print(f"Text: {text}, Distance: {distances1[text]}")

# Вычислим расстояния для второго примера
distances2 = {text: modified_levenshtein_distance(pattern2, text) for text in texts2}
sorted_texts2 = sorted(distances2, key=distances2.get)

print("Пример №2:")
for text in sorted_texts2:
    print(f"Text: {text}, Distance: {distances2[text]}")
