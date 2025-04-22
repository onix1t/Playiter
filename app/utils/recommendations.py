from typing import List
from app.models.game import Game
from app.services.steam import steam_service, logger


def get_recommendations(steam_id: str) -> List[Game]:
    """Улучшенный алгоритм рекомендаций"""
    try:
        # 1. Получаем игры пользователя
        user_games = steam_service.get_user_games(steam_id)
        if not user_games:
            return []

        # 2. Сортируем по дате последнего запуска и берем топ 25
        recently_played = sorted(
            user_games,
            key=lambda x: x.get('rtime_last_played', 0),
            reverse=True
        )[:25]

        # 3. Сортируем по времени игры и берем топ 10
        top_played = sorted(
            recently_played,
            key=lambda x: x.get('playtime_forever', 0),
            reverse=True
        )[:10]

        # 4. Собираем категории из топ 10 игр
        categories = set()
        user_appids = {g['appid'] for g in user_games}

        for game in top_played:
            details = steam_service.get_game_details(game['appid'])
            if details:
                categories.update(details.categories)

        if not categories:
            return []

        # 5. Получаем популярные игры и фильтруем по категориям
        popular_games = steam_service.get_popular_games()
        recommended = []

        for game in popular_games:
            if len(recommended) >= 25:  # Ограничиваем количество проверяемых игр
                break

            if game['appid'] not in user_appids:
                details = steam_service.get_game_details(game['appid'])
                if details and any(cat in details.categories for cat in categories):
                    recommended.append(details)

        # 6. Сортируем по рекомендациям и году выпуска
        recommended.sort(
            key=lambda x: (
                -x.recommendations,
                -x.release_year if x.release_year else 0
            )
        )

        # 7. Возвращаем топ 15 игр
        return recommended[:15]

    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return []