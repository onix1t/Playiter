from typing import List, Dict, Tuple
from ..models.game import Game, RecommendationMetrics
from ..services.steam import steam_service, logger
from concurrent.futures import ThreadPoolExecutor
import time
from ..services.redis import redis_service


def get_recommendations(steam_id: str) -> Tuple[List[Game], RecommendationMetrics]:
    """Улучшенный алгоритм рекомендаций с фильтрацией по времени игры и метриками"""
    start_time = time.time()
    metrics = {
        "input_games_count": 0,
        "filtered_games_count": 0,
        "categories_found": 0,
        "genres_found": 0,
        "popular_games_considered": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "api_errors": 0,
        "execution_time": 0
    }

    try:
        # 1. Параллельно получаем данные
        with ThreadPoolExecutor(max_workers=3) as executor:
            user_games_future = executor.submit(steam_service.get_user_games, steam_id)
            popular_games_future = executor.submit(steam_service.get_popular_games)

            user_games = user_games_future.result()
            popular_games = popular_games_future.result()

        metrics["input_games_count"] = len(user_games)

        # 2. Фильтруем игры с нулевым временем
        user_games = [
            game for game in user_games
            if game.get('playtime_forever', 0) > 0
        ]
        metrics["filtered_games_count"] = len(user_games)

        if not user_games:
            logger.warning(f"No played games found for user {steam_id}")
            return [], _create_metrics(steam_id, start_time, metrics, [], [])

        # 3. Собираем топ игр
        recently_played = sorted(
            user_games,
            key=lambda x: x.get('rtime_last_played', 0),
            reverse=True
        )[:25]

        top_played = sorted(
            recently_played,
            key=lambda x: x.get('playtime_forever', 0),
            reverse=True
        )[:10]

        # 4. Собираем категории и жанры из топовых игр
        user_preferences = set()  # Будет содержать и категории, и жанры
        categories = set()
        genres = set()
        user_appids = {g['appid'] for g in user_games}

        for game in top_played:
            details = steam_service.get_game_details(game['appid'])
            if details:
                if details.categories:
                    categories.update(details.categories)
                    user_preferences.update(details.categories)
                if details.genres:
                    genres.update(details.genres)
                    user_preferences.update(details.genres)

        metrics["categories_found"] = len(categories)
        metrics["genres_found"] = len(genres)

        if not user_preferences:
            return [], _create_metrics(steam_id, start_time, metrics, list(categories), list(genres))

        # 5. Фильтруем популярные игры с учетом и категорий, и жанров
        recommended = []
        metrics["popular_games_considered"] = len(popular_games)

        for game in popular_games:
            if len(recommended) >= 25:
                break

            if game['appid'] not in user_appids:
                details = steam_service.get_game_details(game['appid'])
                if details:
                    # Проверяем совпадение по категориям ИЛИ жанрам
                    has_match = any(
                        pref in details.categories or pref in details.genres
                        for pref in user_preferences
                    )

                    if has_match:
                        recommended.append(details)

        # 6. Сортируем по рейтингу и году
        recommended.sort(
            key=lambda x: (-x.recommendations, -x.release_year if x.release_year else 0)
        )

        metrics["execution_time"] = time.time() - start_time

        return recommended[:30], _create_metrics(
            steam_id,
            start_time,
            metrics,
            list(categories),
            list(genres)
        )

    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        metrics["execution_time"] = time.time() - start_time
        return [], _create_metrics(steam_id, start_time, metrics, [], [])


def _create_metrics(
        steam_id: str,
        start_time: float,
        metrics: Dict,
        categories: List[str],
        genres: List[str]
) -> RecommendationMetrics:
    """Создает объект метрик с разделением категорий и жанров"""
    return RecommendationMetrics(
        user_id=steam_id,
        timestamp=start_time,
        execution_time=metrics["execution_time"],
        input_games_count=metrics["input_games_count"],
        recommended_games_count=metrics.get("filtered_games_count", 0),
        categories_used=categories,
        genres_used=genres,
        metrics=metrics
    )