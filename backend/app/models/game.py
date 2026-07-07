from sqlalchemy import Column, DateTime, Integer, String, func, ForeignKey, Text
from app.core.database import Base

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("users.id"), index = True, nullable = False)
    black_player_id = Column(Integer, ForeignKey("users.id"), index = True, nullable = False)
    status = Column(String(50), default = "waiting", nullable = False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable = True)
    pgn = Column(Text, default = "")
    time_control = Column(String(50), nullable = False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())