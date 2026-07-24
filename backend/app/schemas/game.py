from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class GameCreateRequest(BaseModel):
    opponent_username: str = Field(min_length=3, max_length=50)
    time_control: Literal["rapid", "blitz", "bullet", "classical"]
    play_as: Literal["white", "black"]


class MoveRequest(BaseModel):
    move: str = Field(min_length=4, max_length=5)


class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: int
    status: Literal["active", "completed", "abandoned"]
    winner_id: Optional[int] = None
    current_fen: str
    pgn: str
    time_control: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MoveResponse(BaseModel):
    move: str
    san: str
    game: GameResponse
