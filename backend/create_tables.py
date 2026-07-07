from app.core.database import Base, engine
from app.models.user import User
from app.models.game import Game 

print("Creating database tables...")
Base.metadata.create_all(bind = engine)
print("Tables created successfully.")