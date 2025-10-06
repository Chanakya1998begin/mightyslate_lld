"""Runtime configuration and secrets management."""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ITSMAdapterSettings(BaseSettings):
    """Configuration for ITSM adapter selection and credentials."""

    provider: str = Field(
        default="servicenow",
        description="Identifier for the ITSM adapter implementation to load.",
    )
    instance_url: Optional[str] = Field(default=None, description="Base URL for the ITSM instance.")
    username: Optional[str] = Field(default=None, description="Service account username.")
    password_secret: Optional[str] = Field(
        default=None,
        description="Reference to the password secret in the secrets backend.",
    )


class GlobalAgentPolicies(BaseSettings):
    """Policy flags that govern agent autonomy."""

    enable_auto_remediation: bool = Field(
        default=False,
        description="Allow agents to execute network changes without human approval.",
    )
    remediation_whitelist: List[str] = Field(
        default_factory=list,
        description="List of remediation playbooks that can execute automatically.",
    )


class Settings(BaseSettings):
    """Top-level settings object loaded via environment variables or .env files."""

    log_level: str = Field(default="INFO", description="Default log level for structlog.")
    itsm: ITSMAdapterSettings = Field(default_factory=ITSMAdapterSettings)
    policies: GlobalAgentPolicies = Field(default_factory=GlobalAgentPolicies)

    model_config = {
        "env_prefix": "NETWORK_AUTOMATION_",
        "env_nested_delimiter": "__",
    }


def load_settings() -> Settings:
    """Load configuration using pydantic-settings."""

    return Settings()  # type: ignore[arg-type]
