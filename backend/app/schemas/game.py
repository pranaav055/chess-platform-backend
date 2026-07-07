from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional

class GameCreateRequest(BaseModel):
    opponent_username: str
    time_control: Literal["rapid", "blitz", "bullet", "classical"]
    play_as: Literal["white", "black"]

class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: int 
    status: Literal["waiting", "active", "completed", "abandoned"]
    winner_id: Optional[int] = None
    pgn: str 
    time_control: str 
    created_at: datetime 
    model_config = {"from_attributes": True}