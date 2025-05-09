from dataclasses import Field
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Game(BaseModel):
    steam_appid: int
    name: str
    categories: List[str] = []
    genres: List[str] = []
    recommendations: int = 0
    release_year: Optional[int] = None

    def __str__(self):
        return f"{self.name} (ID: {self.steam_appid})"

class RecommendationMetrics(BaseModel):
    user_id: str
    timestamp: float
    execution_time: float
    input_games_count: int
    recommended_games_count: int
    categories_used: List[str]
    genres_used: List[str]
    metrics: Dict[str, Any]