from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
from app.services.steam import (
    get_user_games_with_details,
    get_popular_games,
    get_game_details
)
from app.utils.recommendations import recommend_games
from app.services.auth import router as auth_router
from app.config import settings

app = FastAPI(
    title="Steam Game Recommender API",
    description="API для рекомендации игр на основе библиотеки Steam",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(auth_router)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    """Кастомный обработчик ошибок с полезными подсказками"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "suggestions": [
                {
                    "action": "Try popular games instead",
                    "endpoint": "/popular-games",
                    "method": "GET"
                },
                {
                    "action": "Check your SteamID",
                    "url": "https://steamid.io/"
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/", tags=["Root"])
async def root():
    """Корневой эндпоинт с информацией об API"""
    return {
        "status": "success",
        "service": "Steam Game Recommender",
        "version": "1.1.0",
        "endpoints": {
            "recommendations": "/recommend/{steam_id}",
            "user_games": "/user/{steam_id}/games",
            "game_info": "/game/{appid}",
            "popular_games": "/popular-games"
        }
    }


@app.get("/recommend/{steam_id}", tags=["Recommendations"])
async def get_recommendations(
        steam_id: str,
        limit: int = Query(5, description="Количество рекомендаций (1-20)", gt=0, le=20),
        min_players: int = Query(10000, description="Минимальное количество игроков", ge=0)
):
    """
    Получить персонализированные рекомендации игр

    - Анализирует игры пользователя за последние 6 месяцев
    - Исключает игры, которые уже есть у пользователя
    - Рекомендует популярные игры с похожими характеристиками
    """
    # Проверка конфигурации API
    if not settings.STEAM_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Steam API key not configured"
        )

    # Получаем топовые игры пользователя
    user_top_games = get_user_games_with_details(steam_id)

    # Если нет недавних игр, предлагаем популярные
    if not user_top_games:
        popular = get_popular_games(limit)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "No recent games found. Showing popular games instead.",
                "games": popular,
                "type": "popular"
            }
        )

    # Получаем популярные игры (исключая owned)
    popular_games = [
        game for game in get_popular_games(200)
        if game["appid"] not in {g["appid"] for g in user_top_games}
           and game.get("players", 0) >= min_players
    ]

    # Если нет подходящих игр для рекомендаций
    if not popular_games:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "No recommendations available. Try lowering min_players.",
                "user_top_games": [
                    {
                        "name": game["name"],
                        "appid": game["appid"],
                        "playtime_hours": game["playtime_hours"]
                    }
                    for game in user_top_games[:3]
                ],
                "type": "no_recommendations"
            }
        )

    # Генерируем рекомендации
    recommendations = recommend_games(
        user_top_games=user_top_games,
        all_games=popular_games,
        limit=min(limit, len(popular_games))
    )

    # Формируем ответ
    return {
        "status": "success",
        "type": "personalized",
        "user": {
            "steam_id": steam_id,
            "games_analyzed": len(user_top_games),
            "most_played_game": {
                "name": user_top_games[0]["name"],
                "playtime_hours": user_top_games[0]["playtime_hours"]
            }
        },
        "recommendations": [
            {
                "game": {
                    "name": game["name"],
                    "appid": game["appid"],
                    "current_players": game.get("players", 0),
                    "store_url": f"https://store.steampowered.com/app/{game['appid']}"
                },
                "match": {
                    "score": round(game.get("match_score", 0), 2),
                    "genres": list(set(user_top_games[0]["genres"]) & set(game.get("genres", []))),
                    "tags": list(set(user_top_games[0]["tags"]) & set(game.get("tags", [])))
                }
            }
            for game in recommendations
        ],
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": {
                "limit": limit,
                "min_players": min_players
            }
        }
    }


@app.get("/user/{steam_id}/games", tags=["User Data"])
async def get_user_games(
        steam_id: str,
        limit: int = Query(5, description="Количество возвращаемых игр", gt=0, le=20)
):
    """Получить информацию о топовых играх пользователя"""
    games = get_user_games_with_details(steam_id)
    if not games:
        raise HTTPException(
            status_code=404,
            detail="No games found for this user"
        )

    return {
        "status": "success",
        "steam_id": steam_id,
        "games": [
            {
                "name": game["name"],
                "appid": game["appid"],
                "playtime_hours": game["playtime_hours"],
                "last_played": datetime.fromtimestamp(game["last_played"]).strftime("%Y-%m-%d"),
                "genres": game["genres"]
            }
            for game in games[:limit]
        ],
        "total_games": len(games)
    }


@app.get("/game/{appid}", tags=["Game Info"])
async def get_game_info(
        appid: int,
        detailed: bool = Query(False, description="Получить полную информацию")
):
    """Получить информацию об игре"""
    details = get_game_details(appid)
    if not details:
        raise HTTPException(
            status_code=404,
            detail="Game not found or failed to fetch details"
        )

    response = {
        "status": "success",
        "appid": appid,
        "name": details.get("name"),
        "genres": details.get("genres", []),
        "current_players": details.get("players", 0),
        "store_url": f"https://store.steampowered.com/app/{appid}"
    }

    if detailed:
        response.update({
            "tags": details.get("tags", []),
            "release_date": details.get("release_date"),
            "developer": details.get("developer"),
            "price": details.get("price")
        })

    return response


@app.get("/popular-games", tags=["Discover"])
async def get_popular_games_endpoint(
        limit: int = Query(10, description="Количество игр (1-50)", gt=0, le=50),
        min_players: int = Query(10000, description="Минимальное число игроков", ge=0)
):
    """Получить текущие популярные игры в Steam"""
    games = get_popular_games(limit=100)  # Берем с запасом для фильтрации

    filtered = [
                   game for game in games
                   if game.get("players", 0) >= min_players
               ][:limit]

    return {
        "status": "success",
        "count": len(filtered),
        "games": [
            {
                "name": game["name"],
                "appid": game["appid"],
                "players": game.get("players", 0),
                "genres": game.get("genres", []),
                "store_url": f"https://store.steampowered.com/app/{game['appid']}"
            }
            for game in filtered
        ],
        "updated_at": datetime.utcnow().isoformat()
    }