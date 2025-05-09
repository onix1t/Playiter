import requests
from typing import List, Dict, Optional
from ..config import settings
from ..services.redis import redis_service
from ..models.game import Game
import logging
import time

logger = logging.getLogger(__name__)


class SteamService:
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.store_url = "https://store.steampowered.com/api"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Whitelist для категорий и жанров
        # Whitelist для категорий (точные названия из Steam)
        self.category_whitelist = {
            # Основные игровые режимы
            'Single-player', 'Multi-player', 'Co-op', 'Online Co-op', 'Local Co-op',
            'Online Multi-Player', 'Local Multi-Player', 'Cross-Platform Multiplayer',
            'MMO', 'PvP', 'PvE', 'Shared/Split Screen',
        }

        # Whitelist для жанров (точные названия из Steam)
        self.genre_whitelist = {
            'Action', 'Adventure', 'Casual', 'Indie', 'Massively Multiplayer',
            'Racing', 'RPG', 'Simulation', 'Sports', 'Strategy',
            'Free to Play', 'Early Access', 'Gore', 'Violent',
            'Nudity', 'Sexual Content', 'Anime', 'Story Rich',
            'Atmospheric', 'Great Soundtrack', 'Pixel Graphics',
            'Classic', 'Retro', '2D', '3D', 'First-Person',
            'Third Person', 'Isometric', 'Top-Down', 'Side Scroller',
            'Survival', 'Horror', 'Sci-fi', 'Fantasy', 'Zombies',
            'Open World', 'Sandbox', 'Space', 'Stealth', 'Hack and Slash',
            'Shooter', 'Fighting', 'Platformer', 'Puzzle', 'Rhythm',
            'Tower Defense', 'Turn-Based', 'Real-Time', 'Tactical',
            'Visual Novel', 'Card Game', 'Board Game', 'MOBA', 'Battle Royale',
            'Military', 'Historical', 'Comedy', 'Cyberpunk', 'Post-apocalyptic',
            'Dystopian', 'Mystery', 'Detective', 'Thriller', 'Western'
        }

    def _filter_categories(self, categories: List[str]) -> List[str]:
        """Фильтрует категории по whitelist"""
        return [cat for cat in categories if cat in self.category_whitelist]

    def _filter_genres(self, genres: List[str]) -> List[str]:
        """Фильтрует жанры по whitelist"""
        return [genre for genre in genres if genre in self.genre_whitelist]

    def get_user_games(self, steam_id: str) -> List[Dict]:
        cache_key = f"user_games:{steam_id}"
        if cached := redis_service.get_cached_data(cache_key):
            return cached

        try:
            response = requests.get(
                f"{self.base_url}/IPlayerService/GetOwnedGames/v1/",
                params={
                    'key': settings.STEAM_API_KEY,
                    'steamid': steam_id,
                    'include_appinfo': 1,
                    'include_played_free_games': 1
                },
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            games = response.json().get('response', {}).get('games', [])
            redis_service.cache_data(cache_key, games, ttl=86400)
            return games
        except requests.exceptions.RequestException as e:
            logger.error(f"Steam API error: {e}")
            return []

    def get_game_details(self, appid: int) -> Optional[Game]:
        """Получаем детали игры с фильтрацией категорий и жанров"""
        cache_key = f"game_details:{appid}"
        cached = redis_service.get_cached_data(cache_key)
        if cached:
            return Game(**cached)

        try:
            time.sleep(0.5)
            url = f"{self.store_url}/appdetails?appids={appid}"
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(5)
                response = requests.get(url, headers=self.headers, timeout=15)

            response.raise_for_status()

            data = response.json().get(str(appid), {})
            if not data or not data.get('success', False):
                return None

            game_data = data.get('data', {})

            # Обработка года выпуска
            release_year = None
            release_date = game_data.get('release_date', {}).get('date', '')
            if release_date:
                try:
                    release_year = int(release_date.split(',')[-1].strip())
                except (ValueError, AttributeError):
                    pass

            # Обработка и фильтрация категорий
            categories = []
            for cat in game_data.get('categories', []):
                if isinstance(cat, dict) and 'description' in cat:
                    categories.append(cat['description'])
            categories = self._filter_categories(categories)

            # Обработка и фильтрация жанров
            genres = []
            for genre in game_data.get('genres', []):
                if isinstance(genre, dict) and 'description' in genre:
                    genres.append(genre['description'])
            genres = self._filter_genres(genres)

            # Обработка рекомендаций
            recommendations = game_data.get('recommendations', {}).get('total', 0)
            if not isinstance(recommendations, int):
                recommendations = 0

            game = Game(
                steam_appid=appid,
                name=game_data.get('name', f"Game {appid}"),
                categories=categories,
                genres=genres,
                recommendations=recommendations,
                release_year=release_year
            )

            redis_service.cache_data(cache_key, game.dict(), 3600)
            return game

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for appid {appid}: {e}")
        except Exception as e:
            logger.error(f"Error processing game {appid}: {e}")

        return None

    def get_popular_games(self) -> List[Dict]:
        """Получаем список популярных игр"""
        cache_key = "popular_games"
        cached = redis_service.get_cached_data(cache_key)
        if cached:
            return cached

        try:
            url = f"{self.base_url}/ISteamChartsService/GetMostPlayedGames/v1/"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            games = response.json().get('response', {}).get('ranks', [])
            redis_service.cache_data(cache_key, games, 7200)
            return games

        except Exception as e:
            logger.error(f"Error fetching popular games: {e}")
            return []


steam_service = SteamService()