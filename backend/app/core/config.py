from pydantic_settings import BaseSettings, SettingsConfigDict 
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/chess_db"
    SECRET_KEY: str = "My_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    model_config = SettingsConfigDict(env_file = ".env", env_file_encoding = "utf-8")

settings = Settings()