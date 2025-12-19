"""Configuration management using Pydantic Settings.

Maintains backward compatibility with existing config.yml format while
supporting environment variable overrides for Docker deployment.
"""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with YAML and environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="SERVICES_",
        env_file=".env",
        extra="ignore",
    )

    # Reports directory
    reports_dir: Path = Field(
        default=Path("/var/log/cisco"),
        description="Directory for PRT and QRT logs",
    )

    # CGI Authentication
    cgi_username: str = Field(default="cisco")
    cgi_password: str = Field(default="cisco")

    # Asterisk Manager Interface
    manager_url: str = Field(default="http://localhost:8088/mxml")
    manager_username: str = Field(default="asterisk")
    manager_secret: str = Field(default="asterisk")

    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=6972)
    reload: bool = Field(default=False)

    # Config file path (for backward compatibility)
    config_file: Path | None = Field(default=None, validation_alias="SERVICES_CONFIG")

    @model_validator(mode="after")
    def load_yaml_config(self) -> "Settings":
        """Load config from YAML file if it exists (backward compatibility)."""
        config_path = self.config_file or Path("config.yml")

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                doc = yaml.safe_load(f)
                if doc:
                    # Map YAML keys to settings (hyphenated keys)
                    if "reports-dir" in doc:
                        self.reports_dir = Path(doc["reports-dir"])
                    if "cgi-username" in doc:
                        self.cgi_username = doc["cgi-username"]
                    if "cgi-password" in doc:
                        self.cgi_password = doc["cgi-password"]
                    if "manager-url" in doc:
                        self.manager_url = doc["manager-url"]
                    if "manager-username" in doc:
                        self.manager_username = doc["manager-username"]
                    if "manager-secret" in doc:
                        self.manager_secret = doc["manager-secret"]

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
