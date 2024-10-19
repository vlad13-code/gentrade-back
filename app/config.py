import sys

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings

# Check if we're in debug mode
# env_file = ".env.debug" if "dev_environment" in sys.argv else ".env"
env_file = ".env"

load_dotenv(find_dotenv(env_file))


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    LANGCHAIN_API_KEY: str
    LANGCHAIN_CALLBACKS_BACKGROUND: bool
    LANGCHAIN_TRACING_V2: bool
    LANGCHAIN_PROJECT: str

    GITHUB_TOKEN: str
    OPENAI_API_KEY: str
    GEOCODE_API_KEY: str
    MODE: str
    CLERK_JWT_KEY: str

    class Config:
        env_file = env_file
        # env_prefix = "DEBUG_" if "dev_environment" in sys.argv else ""

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_psycopg(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
