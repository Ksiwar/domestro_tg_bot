from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Env(Enum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"

class Settings(BaseSettings):
    model_config = SettingsConfigDict()
    env: str
    bot_api_key: str
    mongo_dsn: str
    mongo_db_name: str
    mongo_state_collection: str = "state"
    mongo_timeout_ms: int = 5000
    mongo_connect_timeout_ms:int = 10000
    http_proxy: Optional[str] = None



