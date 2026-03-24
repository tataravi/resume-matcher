from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Application
    app_name: str = Field(default="Resume Analyzer", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"], 
        env="CORS_ORIGINS"
    )
    
    # Security
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    
    # Database
    database_url: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: str = Field(default="test-key", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="test-secret", env="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: str = Field(default="test-bucket", env="AWS_S3_BUCKET")
    aws_dynamodb_table: str = Field(default="test-table", env="AWS_DYNAMODB_TABLE")
    aws_sqs_queue_url: str = Field(default="test-queue", env="AWS_SQS_QUEUE_URL")
    
    # Claude API
    claude_api_key: str = Field(default="test-api-key", env="CLAUDE_API_KEY")
    claude_base_url: str = Field(default="https://api.anthropic.com", env="CLAUDE_BASE_URL")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", env="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=4096, env="CLAUDE_MAX_TOKENS")
    claude_temperature: float = Field(default=0.1, env="CLAUDE_TEMPERATURE")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")


settings = Settings()