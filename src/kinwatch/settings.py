from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", alias="KINWATCH_HOST")
    port: int = Field(default=8000, alias="KINWATCH_PORT")
    public_base_url: str = Field(default="http://127.0.0.1:8000", alias="KINWATCH_PUBLIC_BASE_URL")
    data_dir: Path = Field(default=Path("./data"), alias="KINWATCH_DATA_DIR")
    household_tz: str = Field(default="America/Los_Angeles", alias="KINWATCH_HOUSEHOLD_TZ")
    use_fixtures: bool = Field(default=True, alias="KINWATCH_USE_FIXTURES")

    ring_api_base: str = Field(default="https://api.amazonvision.com", alias="RING_API_BASE")
    ring_oauth_token_url: str = Field(default="https://oauth.ring.com/oauth/token", alias="RING_OAUTH_TOKEN_URL")
    ring_access_token: str = Field(default="", alias="RING_ACCESS_TOKEN")
    ring_refresh_token: str = Field(default="", alias="RING_REFRESH_TOKEN")
    ring_client_id: str = Field(default="", alias="RING_CLIENT_ID")
    ring_client_secret: str = Field(default="", alias="RING_CLIENT_SECRET")
    ring_hmac_key: str = Field(default="fixture-hmac-key", alias="RING_HMAC_KEY")
    ring_audio_ref: str = Field(default="kinwatch-looking", alias="RING_AUDIO_REF")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    bedrock_vision_model: str = Field(default="amazon.nova-lite-v1:0", alias="KINWATCH_BEDROCK_VISION_MODEL")
    bedrock_speech_model: str = Field(default="amazon.nova-sonic-v1:0", alias="KINWATCH_BEDROCK_SPEECH_MODEL")
    polly_voice: str = Field(default="Joanna", alias="KINWATCH_POLLY_VOICE")
    ddb_table: str = Field(default="", alias="KINWATCH_DDB_TABLE")
    strands_model: str = Field(default="amazon.nova-pro-v1:0", alias="KINWATCH_STRANDS_MODEL")

    def ensure_data_dir(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


def get_settings() -> Settings:
    return Settings()
