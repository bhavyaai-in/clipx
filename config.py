from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    admin_email: str
    admin_password: str
    jwt_secret: str
    files_dir: str = "uploads"
    file_ttl_minutes: int = 30
    webhook_secret: str = ""
    github_token: str = ""
    repo_url: str = "github.com/bhavyaai-in/clipx.git"
    repo_path: str = "/home/bhavyaai/public_html/bbhavyaai.com"
    subfolder_path: str = "build_folder/standalone"

    class Config:
        env_file = ".env"

settings = Settings()
