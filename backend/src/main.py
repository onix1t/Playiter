from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .services.steam import steam_service
from .utils.recommendations import get_recommendations
from .services.auth import router as auth_router

app = FastAPI(
    title="Steam Game Recommender",
    version="1.0"
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
        "service": "Steam Game Recommender",
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
            for g in sorted(games, key=lambda x: x.get('rtime_last_played', 0), reverse=True)[:5]
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
        recommendations = get_recommendations(steam_id)
        return {
            "steam_id": steam_id,
            "recommendations": [
                {
                    "name": game.name,
                    "appid": game.steam_appid,
                    "categories": game.categories,
                    "recommendations": game.recommendations,
                    "release_year": game.release_year,
                    "store_url": f"https://store.steampowered.com/app/{game.steam_appid}"
                }
                for game in recommendations
            ],
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))