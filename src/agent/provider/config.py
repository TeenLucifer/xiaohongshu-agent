"""Provider configuration."""

from __future__ import annotations

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent.errors import RuntimeInitializationError


class ProviderConfig(BaseSettings):
    """OpenAI-compatible provider configuration."""

    api_key: str = Field(alias="OPENAI_API_KEY", min_length=1)
    base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    model: str = Field(alias="OPENAI_MODEL", min_length=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @classmethod
    def load(cls, **overrides: str | None) -> ProviderConfig:
        """Load provider config from env/.env with optional explicit overrides."""

        filtered = {key: value for key, value in overrides.items() if value is not None}
        try:
            return cls(**filtered)
        except ValidationError as exc:
            missing = sorted(
                {
                    str(item["loc"][0])
                    for item in exc.errors()
                    if item["type"] == "missing" and item["loc"]
                }
            )
            if missing:
                joined = ", ".join(missing)
                raise RuntimeInitializationError(f"缺少 provider 配置: {joined}") from exc
            raise RuntimeInitializationError(f"provider 配置无效: {exc}") from exc
