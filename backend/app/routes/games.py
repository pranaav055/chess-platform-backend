import chess
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.game import Game
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.game import (
    GameCreateRequest,
    GameResponse,
    MoveRequest,
    MoveResponse,
)
from app.services.chess_service import (
    IllegalMoveError,
    InvalidBoardStateError,
    InvalidMoveFormatError,
    apply_move,
    load_board,
    update_pgn,
    winner_player_id,
)

router = APIRouter(prefix="/games", tags=["games"])


def ensure_participant(game: Game, user_id: int) -> None:
    if user_id not in (game.white_player_id, game.black_player_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only players in this game can access it",
        )


@router.post(
    "/create",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_game(
    game_data: GameCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Game:
    opponent = (
        db.query(User).filter(User.username == game_data.opponent_username).first()
    )
    if opponent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opponent not found",
        )
    if opponent.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot create a game against yourself",
        )

    if game_data.play_as == "white":
        white_id, black_id = current_user.id, opponent.id
    else:
        white_id, black_id = opponent.id, current_user.id

    game = Game(
        white_player_id=white_id,
        black_player_id=black_id,
        time_control=game_data.time_control,
        status="active",
        current_fen=chess.STARTING_FEN,
    )
    db.add(game)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create game",
        )
    db.refresh(game)
    return game


@router.get("/my-games", response_model=list[GameResponse])
def get_my_games(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Game]:
    return (
        db.query(Game)
        .filter(
            or_(
                Game.white_player_id == current_user.id,
                Game.black_player_id == current_user.id,
            )
        )
        .all()
    )


@router.post("/{game_id}/move", response_model=MoveResponse)
def make_move(
    game_id: int,
    move_data: MoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    game = db.query(Game).filter(Game.id == game_id).with_for_update().first()
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )

    ensure_participant(game, current_user.id)
    if game.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This game is no longer active",
        )

    try:
        board = load_board(game.current_fen)
    except InvalidBoardStateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored game state is invalid",
        )

    expected_player_id = (
        game.white_player_id if board.turn == chess.WHITE else game.black_player_id
    )
    if current_user.id != expected_player_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="It is not your turn",
        )

    previous_fen = game.current_fen
    try:
        applied = apply_move(board, move_data.move)
        new_pgn = update_pgn(
            game.pgn,
            previous_fen,
            applied.move,
            applied.outcome,
        )
    except InvalidMoveFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except IllegalMoveError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except InvalidBoardStateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored game history is inconsistent",
        )

    game.current_fen = applied.current_fen
    game.pgn = new_pgn
    if applied.outcome is not None:
        game.status = "completed"
        game.winner_id = winner_player_id(
            applied.outcome,
            game.white_player_id,
            game.black_player_id,
        )

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save move",
        )
    db.refresh(game)
    return {"move": move_data.move, "san": applied.san, "game": game}


@router.get("/{game_id}", response_model=GameResponse)
def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Game:
    game = db.query(Game).filter(Game.id == game_id).first()
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )
    ensure_participant(game, current_user.id)
    return game
