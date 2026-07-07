from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List 

from app.core.database import get_db
from app.models.game import Game
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.game import GameCreateRequest, GameResponse

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/create", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(game_data: GameCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opponent_user = db.query(User).filter(User.username == game_data.opponent_username).first()

    if not opponent_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid opponent")
    
    if opponent_user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid opponent")
    
    user_colour = game_data.play_as
    if user_colour == "white":
        white_id = current_user.id
        black_id = opponent_user.id
    else:
        white_id = opponent_user.id
        black_id = current_user.id
    
    new_game = Game(white_player_id=white_id, black_player_id=black_id, time_control=game_data.time_control)
    
    db.add(new_game)
    db.commit()
    db.refresh(new_game)

    return new_game

@router.get("/my-games", response_model=List[GameResponse])
def get_my_game(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
     user_id = current_user.id
     games = db.query(Game).filter(or_(Game.white_player_id == user_id, Game.black_player_id == user_id)).all()
     return games


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user_id = current_user.id
    if user_id != game.white_player_id and user_id != game.black_player_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return game