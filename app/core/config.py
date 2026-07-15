from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config=SettingsConfigDict(env_file=".env",extra="ignore")

    LLM_PROVIDER:str="groq"
    LLM_MODEL:str="groq/llama-3.3-70b-versatile"
    GROQ_API_KEY:str=""

    APP_HOST:str="0.0.0.0"
    APP_PORT:int=8000
    LOG_LEVEL:str="INFO"

    SESSION_DIR:str="app/data/sessions"
    FAQ_FILE:str="app/data/faqs.json"

    MAX_JUDGE_RETRIES:int=2


settings=Settings()
