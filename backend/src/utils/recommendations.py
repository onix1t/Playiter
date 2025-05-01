from typing import List, Dict
from ..models.game import Game
from ..services.steam import steam_service, logger
from concurrent.futures import ThreadPoolExecutor


def get_recommendations(steam_id: str) -> List[Game]:
    """Улучшенный алгоритм рекомендаций с фильтрацией по времени игры"""
    try:
        # 1. Параллельно получаем данные
        with ThreadPoolExecutor(max_workers=3) as executor:
            user_games_future = executor.submit(steam_service.get_user_games, steam_id)
            popular_games_future = executor.submit(steam_service.get_popular_games)

            user_games = user_games_future.result()
            popular_games = popular_games_future.result()

        # 2. Фильтруем игры с нулевым временем (playtime_forever в минутах)
        user_games = [
            game for game in user_games
            if game.get('playtime_forever', 0) > 0  # Удаляем игры с 0 минут
        ]

        if not user_games:
            logger.warning(f"No played games found for user {steam_id}")
            return []

        # 3. Собираем топ игр (уже без нулевых)
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

        # 4. Собираем категории из топовых игр
        categories = set()
        user_appids = {g['appid'] for g in user_games}

        for game in top_played:
            details = steam_service.get_game_details(game['appid'])
            if details:
                categories.update(details.categories)

        if not categories:
            return []

        # 5. Фильтруем популярные игры
        recommended = []
        for game in popular_games:
            if len(recommended) >= 25:
                break

            if game['appid'] not in user_appids:
                details = steam_service.get_game_details(game['appid'])
                if details and any(cat in details.categories for cat in categories):
                    recommended.append(details)

        # 6. Сортируем по рейтингу и году
        recommended.sort(
            key=lambda x: (-x.recommendations, -x.release_year if x.release_year else 0)
        )

        return recommended[:30]

    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return []