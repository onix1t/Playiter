from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.src.main import app
from backend.src.models.game import Game, RecommendationMetrics

client = TestClient(app)

TEST_STEAM_ID = "76561197960434622"
TEST_APP_ID = 730


def test_login_redirect():
    response = client.get("/login", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert "steamcommunity.com/openid" in response.headers.get("location", "")


@patch("backend.src.main.steam_service.get_user_games")
def test_user_info(mock_get_user_games):
    mock_get_user_games.return_value = [
        {"appid": 123, "name": "Test Game", "playtime_forever": 120, "rtime_last_played": 1234567890}
    ]
    response = client.get(f"/user/{TEST_STEAM_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["steam_id"] == TEST_STEAM_ID
    assert isinstance(data["recent_games"], list)


@patch("backend.src.main.steam_service.get_game_details")
def test_game_info(mock_get_game_details):
    mock_get_game_details.return_value = Game(
        steam_appid=TEST_APP_ID,
        name="Mocked Game",
        categories=["Single-player"],
        genres=["RPG"],
        recommendations=123,
        release_year=2020
    )

    response = client.get(f"/game/{TEST_APP_ID}")
    assert response.status_code == 200
    json = response.json()
    assert json["name"] == "Mocked Game"
    assert json["steam_appid"] == TEST_APP_ID


@patch("backend.src.main.get_recommendations")
@patch("backend.src.main.redis_service.cache_data")
def test_recommendations(mock_cache_data, mock_get_recommendations):
    mock_game = Game(
        name="Game A",
        steam_appid=123,
        categories=["Action"],
        genres=["Shooter"],
        recommendations=100,
        release_year=2021
    )

    mock_metrics = RecommendationMetrics(
        user_id="test_user",
        timestamp=1234567890,
        execution_time=0.01,
        input_games_count=10,
        recommended_games_count=1,
        categories_used=["Action"],
        genres_used=["Shooter"],
        metrics={"execution_time": 0.01}
    )

    mock_get_recommendations.return_value = ([mock_game], mock_metrics)

    response = client.get(f"/recommend/{TEST_STEAM_ID}")
    assert response.status_code == 200
    json = response.json()
    assert json["count"] == 1
    assert json["recommendations"][0]["name"] == "Game A"


@patch("backend.src.main.redis_service.client.keys")
@patch("backend.src.main.redis_service.get_cached_data")
def test_metrics(mock_get_cached_data, mock_keys):
    mock_keys.return_value = [f"metrics:{TEST_STEAM_ID}:123"]
    mock_get_cached_data.return_value = {"mock": "metric"}
    response = client.get(f"/metrics/{TEST_STEAM_ID}")
    assert response.status_code == 200
    json = response.json()
    assert "metrics" in json
    assert isinstance(json["metrics"], list)
    assert json["metrics"][0] == {"mock": "metric"}
