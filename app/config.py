from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/meetheman'
    jwt_secret: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    token_expire_minutes: int = 60 * 24
    allowed_school_domains: str = 'school.edu,university.edu'
    rate_limit_per_minute: int = 120


settings = Settings()
