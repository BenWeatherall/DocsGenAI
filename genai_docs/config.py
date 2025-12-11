"""
Configuration management for GenAI Docs.

This module handles all configuration settings including API keys,
model settings, and project configuration.
"""

import os
from pathlib import Path
from typing import Optional

from .exceptions import ConfigurationError


class Config:
    """Configuration manager for GenAI Docs."""

    def __init__(self):
        """Initialize configuration with default values."""
        self.api_key: Optional[str] = None
        self.model_name: str = "gemini-2.0-flash"
        self.project_root: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.use_cache: bool = True
        self.force_regenerate: bool = False
        self.use_dependency_graph: bool = True
        self.verbose: bool = False

    def load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ConfigurationError(
                "GOOGLE_API_KEY environment variable is required. "
                "Please set it with: export GOOGLE_API_KEY='your-api-key-here'"
            )

    def set_project_root(self, project_path: str) -> None:
        """Set the project root path."""
        self.project_root = Path(project_path).resolve()
        if not self.project_root.is_dir():
            raise ConfigurationError(
                f"Project path is not a valid directory: {project_path}"
            )

    def set_output_dir(self, output_path: Optional[str] = None) -> None:
        """Set the output directory for documentation."""
        if output_path:
            self.output_dir = Path(output_path).resolve()
        else:
            self.output_dir = self.project_root

    def get_documentation_path(self, module_path: Path) -> Path:
        """Get the path where documentation should be saved for a module."""
        if self.output_dir and self.project_root:
            # If output_dir is set, maintain relative structure
            try:
                rel_path = module_path.relative_to(self.project_root)
                return self.output_dir / rel_path
            except ValueError:
                # If paths are not related, use output_dir directly
                return self.output_dir
        return module_path


# Global configuration instance
config = Config()
