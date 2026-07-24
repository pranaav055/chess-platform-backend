import chess
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.core.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )
    black_player_id = Column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )
    status = Column(String(50), default="active", nullable=False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    current_fen = Column(Text, default=chess.STARTING_FEN, nullable=False)
    pgn = Column(Text, default="", nullable=False)
    time_control = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
