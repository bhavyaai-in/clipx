from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    admin_email: str
    admin_password: str
    jwt_secret: str
    files_dir: str = "uploads"
    file_ttl_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
