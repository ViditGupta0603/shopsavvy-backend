from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    
    # MongoDB settings
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "shopsavvy"
    
    # JWT settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App settings
    app_name: str = "ShopSavvy API"
    debug: bool = False

settings = Settings()
