import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class AppSettings(BaseModel):
    name: str = "Data Layer Manager"
    version: str = "0.0.1"


class EmbeddingSettings(BaseModel):
    provider: str = "huggingface"
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32


class ChunkingSettings(BaseModel):
    default_size: int = 500
    default_overlap: int = 50


class VectorStoreSettings(BaseModel):
    provider: str = "pgvector"


class DatabaseSettings(BaseModel):
    db_type: str = "postgresql"
    # Secrets should come from .env
    url: str | None = Field(default=None, validation_alias="DATABASE_URL")


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A custom settings source that loads configuration from YAML files.
    Support: settings.yaml + settings.{env}.yaml
    """

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        self.config_dir = Path("config")
        self.app_env = os.getenv("APP_ENV", "dev").lower()
        self._config_data = self._load_all_configs()

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r") as f:
            return yaml.safe_load(f) or {}

    def _load_all_configs(self) -> dict[str, Any]:
        # 1. Load base settings
        base_configs = self._load_yaml(self.config_dir / "settings.yaml")

        # 2. Load env-specific settings
        env_configs = self._load_yaml(self.config_dir / f"settings.{self.app_env}.yaml")

        # Merge (env overrides base)
        # Deep merge for nested models
        def deep_merge(
            base: dict[str, Any], overrides: dict[str, Any]
        ) -> dict[str, Any]:
            for key, value in overrides.items():
                if (
                    isinstance(value, dict)
                    and key in base
                    and isinstance(base[key], dict)
                ):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        return deep_merge(base_configs, env_configs)

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        """
        Retrieves a field value from the loaded YAML configuration.
        """
        if self._config_data is None:
            return None, field_name, False

        value = self._config_data.get(field_name)
        return value, field_name, False

    def __call__(self) -> dict[str, Any]:
        return self._config_data


class Settings(BaseSettings):
    """
    Main Settings entry point. Uses YAML and Environment Variables.
    """

    app: AppSettings = AppSettings()
    embeddings: EmbeddingSettings = EmbeddingSettings()
    chunking: ChunkingSettings = ChunkingSettings()
    vector_store: VectorStoreSettings = VectorStoreSettings()
    database: DatabaseSettings = DatabaseSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Singleton getter for settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
