from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./app.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24 * 7  # 7 days (demo)

    vectorstore_dir: str = "./vectorstore"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    rag_top_k: int = 25

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None


settings = Settings()

