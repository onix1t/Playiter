from pydantic import BaseModel
from typing import List, Optional

class Game(BaseModel):
    steam_appid: int
    name: str
    categories: List[str] = []
    recommendations: int = 0
    release_year: Optional[int] = None  # Теперь храним только год

    def __str__(self):
        return f"{self.name} (ID: {self.steam_appid})"