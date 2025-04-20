import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.config import settings
from app.services.redis import redis_service
import logging

logger = logging.getLogger(__name__)


def get_game_details(appid: int) -> Optional[Dict]:
    """Получаем детали игры с информацией об игроках"""
    cache_key = f"game_details:{appid}"
    cached = redis_service.get_cached_data(cache_key)
    if cached:
        logger.debug(f"Using cached data for game {appid}")
        return cached

    try:
        # Получаем базовую информацию об игре
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get(str(appid), {}).get("data", {})

        # Получаем количество игроков
        players_url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
        players_response = requests.get(players_url, timeout=5)
        players_data = players_response.json().get("response", {})
        current_players = players_data.get("player_count", 0)

        # Формируем структуру данных
        details = {
            "appid": appid,
            "name": data.get("name"),
            "genres": [g["description"] for g in data.get("genres", [])],
            "tags": list(data.get("tags", {}).keys()) if isinstance(data.get("tags"), dict) else [],
            "release_date": data.get("release_date", {}).get("date"),
            "current_players": current_players,
            "last_updated": int(time.time())
        }

        # Кэшируем на 1 час
        redis_service.cache_data(cache_key, details, 3600)
        logger.debug(f"Cached game details for {appid}")
        return details

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching game details for {appid}: {e}")
    except Exception as e:
        logger.error(f"Error processing game details for {appid}: {e}")

    return None


def get_user_games_with_details(
        steam_id: str,
        recent_only: bool = True,
        limit: int = 15
) -> List[Dict]:
    """Получаем игры пользователя с возможностью отключения фильтров"""
    cache_key = f"user_games:{steam_id}:{recent_only}:{limit}"
    cached = redis_service.get_cached_data(cache_key)
    if cached:
        logger.debug(f"Using cached games for user {steam_id}")
        return cached

    try:
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={settings.STEAM_API_KEY}&steamid={steam_id}&include_appinfo=1&include_played_free_games=1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json().get("response", {}).get("games", [])
        logger.debug(f"Raw Steam API response for {steam_id}: {len(data)} games found")

        # Применяем фильтры
        if recent_only:
            six_months_ago = int((datetime.now() - timedelta(days=180)).timestamp())
            filtered_games = [
                game for game in data
                if game.get("rtime_last_played", float('inf')) >= six_months_ago
            ]
            logger.debug(f"After recent filter: {len(filtered_games)} games remain")
        else:
            filtered_games = data

        # Сортируем по времени игры и дате последнего запуска
        sorted_games = sorted(
            filtered_games,
            key=lambda x: (-x.get("playtime_forever", 0),
                           -x.get("rtime_last_played", 0))
        )[:limit]

        # Получаем детали для каждой игры
        detailed_games = []
        for game in sorted_games:
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

        logger.debug(f"Final games list: {len(detailed_games)} games with details")

        # Кэшируем на 1 день
        redis_service.cache_data(cache_key, detailed_games, 86400)
        return detailed_games

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching games for {steam_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing games for {steam_id}: {e}")

    return []


def get_popular_games(limit: int = 200) -> List[Dict]:
    """Получаем популярные игры с актуальными данными"""
    cache_key = f"steam_popular_games:{limit}"
    cached = redis_service.get_cached_data(cache_key)
    if cached:
        logger.debug("Using cached popular games")
        return cached

    try:
        # Получаем список популярных игр
        charts_url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
        response = requests.get(charts_url, timeout=10)
        response.raise_for_status()

        games_data = response.json().get("response", {}).get("ranks", [])[:limit * 2]
        logger.debug(f"Found {len(games_data)} popular games from Steam API")

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
                time.sleep(0.1)  # Ограничение запросов

        # Сортируем по количеству игроков
        popular_games.sort(key=lambda x: x["current_players"], reverse=True)
        final_list = popular_games[:limit]
        logger.debug(f"Final popular games list: {len(final_list)} games")

        # Кэшируем на 2 часа
        redis_service.cache_data(cache_key, final_list, 7200)
        return final_list

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching popular games: {e}")
    except Exception as e:
        logger.error(f"Error processing popular games: {e}")

    # Fallback
    return get_fallback_popular_games(limit)


def get_fallback_popular_games(limit: int) -> List[Dict]:
    """Резервный список популярных игр"""
    logger.warning("Using fallback popular games list")
    return [
               {"appid": 570, "name": "Dota 2", "current_players": 500000},
               {"appid": 730, "name": "Counter-Strike 2", "current_players": 450000},
               {"appid": 578080, "name": "PUBG", "current_players": 300000}
           ][:limit]