from pydantic import BaseModel
from typing import Optional, List

class Game(BaseModel):
    """Модель для хранения данных об игре"""
    appid: int
    name: Optional[str] = None
    playtime: Optional[int] = 0
    genres: List[str] = []
    tags: List[str] = []

    def __str__(self):
        return f"{self.name or 'Unknown'} (ID: {self.appid})"