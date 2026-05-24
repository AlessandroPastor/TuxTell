from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    storage_type: str = "local"
    storage_local_path: str = "/app/uploads"

    whatsapp_provider: str = "evolution"
    whatsapp_instance_url: str = ""
    whatsapp_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
