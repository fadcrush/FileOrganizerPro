"""Configuration management - Load and validate application settings."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AppConfig:
    """Application configuration container."""

    operation_mode: str = "move"  # move or copy
    organization_mode: str = "category_year"  # category, year, or category_year
    skip_duplicates: bool = True
    create_backup: bool = True
    dry_run: bool = True
    excluded_patterns: list = None
    theme: str = "dark"

    def __post_init__(self):
        if self.excluded_patterns is None:
            self.excluded_patterns = []


class ConfigManager:
    """Manage application configuration.

    Loads and saves configuration from/to files (JSON, YAML, env vars).
    """

    @staticmethod
    def load() -> AppConfig:
        """Load configuration from default sources.

        Returns:
            AppConfig with loaded settings
        """
        # TODO: Load from config files, environment variables, user preferences
        return AppConfig()

    @staticmethod
    def save(config: AppConfig) -> None:
        """Save configuration to persistent storage.

        Args:
            config: Configuration to save
        """
        # TODO: Save to config files
        pass
