from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import numpy as np


def recommend_games(
        user_top_games: List[Dict],
        all_games: List[Dict],
        limit: int = 5
) -> List[Dict]:
    """Улучшенный алгоритм рекомендаций с учетом:
    - схожести жанров/тегов
    - количества текущих игроков
    - актуальности игры
    """
    if not user_top_games or not all_games:
        return []

    # Исключаем игры, которые уже есть у пользователя
    user_appids = {game["appid"] for game in user_top_games}
    available_games = [g for g in all_games if g["appid"] not in user_appids]

    if not available_games:
        return []

    # Собираем "профиль" пользователя на основе топовых игр
    profile_features = []
    for game in user_top_games[:3]:  # Берем топ-3 игры для анализа
        profile_features.extend(game.get("genres", []))
        profile_features.extend(game.get("tags", []))

    if not profile_features:
        return available_games[:limit]

    # Подготовка данных для сравнения
    game_texts = [" ".join(profile_features)]
    game_players = []
    for game in available_games:
        features = game.get("genres", []) + game.get("tags", [])
        game_texts.append(" ".join(features) or "unknown")
        game_players.append(game.get("current_players", 0))

    try:
        # Векторизация текстовых признаков
        vectorizer = TfidfVectorizer(min_df=1, stop_words="english")
        vectors = vectorizer.fit_transform(game_texts)

        # Расчет схожести
        similarity = cosine_similarity(vectors[0:1], vectors[1:])[0]

        # Нормализация количества игроков (0-1)
        max_players = max(game_players) or 1
        normalized_players = np.array([p / max_players for p in game_players])

        # Комбинированная оценка (50% схожесть + 50% популярность)
        combined_scores = 0.5 * similarity + 0.5 * normalized_players

        # Сортировка по комбинированной оценке
        scored_games = sorted(
            zip(available_games, combined_scores),
            key=lambda x: x[1],
            reverse=True
        )

        # Формируем результат с дополнительной информацией
        recommendations = []
        for game, score in scored_games[:limit]:
            game["match_score"] = float(score)
            recommendations.append(game)

        return recommendations

    except Exception as e:
        print(f"Recommendation error: {e}")
        # Fallback: сортируем по количеству игроков
        return sorted(available_games, key=lambda x: x.get("current_players", 0), reverse=True)[:limit]