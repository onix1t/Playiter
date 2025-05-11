from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .services.steam import steam_service
from .utils.recommendations import get_recommendations
from .services.auth import router as auth_router
from .services.redis import redis_service

app = FastAPI(
    title="Playiter",
    version="1.0.3"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "service": "Playiter",
        "endpoints": {
            "user_info": "/user/{steam_id}",
            "game_info": "/game/{appid}",
            "recommendations": "/recommend/{steam_id}"
        }
    }


@app.get("/user/{steam_id}")
async def get_user_info(steam_id: str):
    games = steam_service.get_user_games(steam_id)
    if not games:
        raise HTTPException(status_code=404, detail="User not found or no games")

    return {
        "steam_id": steam_id,
        "game_count": len(games),
        "recent_games": [
            {
                "appid": g['appid'],
                "name": g.get('name', f"AppID {g['appid']}"),
                "playtime_hours": g.get('playtime_forever', 0) // 60,
                "last_played": g.get('rtime_last_played', 0)
            }
            for g in sorted(games, key=lambda x: x.get('rtime_last_played', 0), reverse=True)[:20]
        ]
    }


@app.get("/game/{appid}")
async def get_game_info(appid: int):
    game = steam_service.get_game_details(appid)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return game.dict()


@app.get("/recommend/{steam_id}")
async def get_game_recommendations(steam_id: str):
    try:
        recommendations, metrics = get_recommendations(steam_id)

        # Сохраняем метрики в Redis
        metrics_key = f"metrics:{steam_id}:{int(metrics.timestamp)}"
        redis_service.cache_data(metrics_key, metrics.dict(), ttl=604800)

        return {
            "steam_id": steam_id,
            "recommendations": [
                {
                    "name": game.name,
                    "appid": game.steam_appid,
                    "categories": game.categories,
                    "genres": game.genres,
                    "recommendations": game.recommendations,
                    "release_year": game.release_year,
                    "store_url": f"https://store.steampowered.com/app/{game.steam_appid}"
                }
                for game in recommendations
            ],
            "count": len(recommendations),
            "metrics": metrics.metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/{steam_id}")
async def get_recommendation_metrics(steam_id: str, limit: int = 10):
    try:
        pattern = f"metrics:{steam_id}:*"
        keys = redis_service.client.keys(pattern)

        if not keys:
            return {"message": "No metrics found for this user"}

        keys = sorted(keys, reverse=True)[:limit]
        metrics = []

        for key in keys:
            data = redis_service.get_cached_data(key)
            if data:
                metrics.append(data)

        return {
            "steam_id": steam_id,
            "count": len(metrics),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))