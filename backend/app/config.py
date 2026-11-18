from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    llm_provider: str = "mock"  # mock | openrouter | openai
    openrouter_api_key: str = ""
    openrouter_base_url: str = "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)"
    openrouter_model: str = "openrouter/free"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_provider: str = "local"  # local | openrouter | openai
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openrouter_embedding_model: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    faiss_top_k: int = 5
    bm25_top_k: int = 5
    rrf_k: int = 60
    reranker_enabled: bool = False
    data_dir: str = "./data"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()