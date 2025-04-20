import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.config import settings
from app.services.redis import redis_service

def get_game_details(appid: int) -> Optional[Dict]:
    """Получаем детали игры с информацией об игроках"""
    cached = redis_service.get_cached_data(f"game_details:{appid}")
    if cached:
        return cached

    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url, timeout=10)
        data = response.json().get(str(appid), {}).get("data", {})

        # Получаем текущее количество игроков через Steam API
        players_url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
        players_response = requests.get(players_url, timeout=5)
        players_data = players_response.json().get("response", {})
        current_players = players_data.get("player_count", 0)

        details = {
            "name": data.get("name"),
            "genres": [g["description"] for g in data.get("genres", [])],
            "tags": list(data.get("tags", {}).keys()) if isinstance(data.get("tags"), dict) else [],
            "release_date": data.get("release_date", {}).get("date"),
            "current_players": current_players,
            "last_updated": int(time.time())
        }

        redis_service.cache_data(f"game_details:{appid}", details, 3600)  # Кэш на 1 час
        return details

    except Exception as e:
        print(f"Error fetching game details for {appid}: {e}")
        return None

def get_user_games_with_details(steam_id: str) -> List[Dict]:
    """Получаем игры пользователя с приоритетом по дате и времени игры"""
    cache_key = f"user_games:{steam_id}"
    cached = redis_service.get_cached_data(cache_key)
    if cached:
        return cached

    try:
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={settings.STEAM_API_KEY}&steamid={steam_id}&include_appinfo=1&include_played_free_games=1"
        response = requests.get(url, timeout=15)
        data = response.json().get("response", {}).get("games", [])

        # Фильтрация: играл в последние 6 месяцев
        six_months_ago = int((datetime.now() - timedelta(days=180)).timestamp())
        recent_games = [game for game in data if game.get("rtime_last_played", 0) >= six_months_ago]

        if not recent_games:
            return []

        # Сначала сортируем по дате последнего запуска (новые сверху)
        sorted_by_date = sorted(
            recent_games,
            key=lambda x: x.get("rtime_last_played", 0),
            reverse=True
        )

        # Затем берем топ-15 по времени игры среди недавних
        top_played = sorted(
            sorted_by_date[:50],  # Берем больше для выборки
            key=lambda x: x.get("playtime_forever", 0),
            reverse=True
        )[:15]

        # Получаем детали для игр
        detailed_games = []
        for game in top_played:
            details = get_game_details(game["appid"])
            if details:
                game_data = {
                    "appid": game["appid"],
                    "name": game.get("name", details.get("name", f"AppID {game['appid']}")),
                    "playtime_hours": game.get("playtime_forever", 0) // 60,
                    "last_played": game.get("rtime_last_played", 0),
                    "genres": details.get("genres", []),
                    "tags": details.get("tags", []),
                    "current_players": details.get("current_players", 0)
                }
                detailed_games.append(game_data)

        # Финальная сортировка: сначала недавно играемые, затем по времени игры
        detailed_games.sort(
            key=lambda x: (-x["last_played"], -x["playtime_hours"])
        )

        redis_service.cache_data(cache_key, detailed_games, 86400)  # Кэш на 1 день
        return detailed_games

    except Exception as e:
        print(f"Error fetching user games for {steam_id}: {e}")
        return []

def get_popular_games(limit: int = 200) -> List[Dict]:
    """Получаем популярные игры с актуальными данными об игроках"""
    cache_key = f"steam_popular_games_v2"
    cached = redis_service.get_cached_data(cache_key)
    if cached:
        return cached[:limit]

    try:
        # Источник 1: Steam Charts API
        charts_url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
        response = requests.get(charts_url, timeout=10)
        games_data = response.json().get("response", {}).get("ranks", [])[:limit*2]

        # Если нет данных, используем fallback
        if not games_data:
            raise ValueError("Empty response from Steam Charts")

        # Получаем детали для каждой игры
        popular_games = []
        for game in games_data:
            details = get_game_details(game["appid"])
            if details and details.get("current_players", 0) > 0:
                game_data = {
                    "appid": game["appid"],
                    "name": details.get("name"),
                    "genres": details.get("genres", []),
                    "tags": details.get("tags", []),
                    "current_players": details.get("current_players", 0),
                    "last_updated": details.get("last_updated", 0)
                }
                popular_games.append(game_data)
                time.sleep(0.2)  # Ограничение запросов

        # Сортируем по количеству игроков
        popular_games.sort(key=lambda x: x["current_players"], reverse=True)

        # Кэшируем на 2 часа
        redis_service.cache_data(cache_key, popular_games, 7200)
        return popular_games[:limit]

    except Exception as e:
        print(f"Error fetching popular games: {e}")
        # Fallback: используем кэшированные данные или hardcoded
        return cached[:limit] if cached else get_fallback_popular_games(limit)

def get_fallback_popular_games(limit: int) -> List[Dict]:
    """Fallback-список популярных игр"""
    fallback_games = [
        {"appid": 570, "name": "Dota 2", "current_players": 500000},
        {"appid": 730, "name": "Counter-Strike 2", "current_players": 450000},
        {"appid": 578080, "name": "PUBG", "current_players": 300000}
    ]
    return fallback_games[:limit]