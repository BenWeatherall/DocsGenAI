"""
Unit tests for the configuration module.

This module tests the configuration management functionality
including environment variable loading and validation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from genai_docs.config import Config


class TestConfig:
    """Test the Config class."""

    def test_config_initialization(self):
        """Test Config initialization with default values."""
        config = Config()

        assert config.api_key is None
        assert config.model_name == "gemini-2.0-flash"
        assert config.project_root is None
        assert config.output_dir is None

    def test_load_from_environment(self):
        """Test loading configuration from environment variables."""
        config = Config()

        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'test-api-key',
            'GENAI_MODEL': 'test-model'
        }):
            config.load_from_environment()

        assert config.api_key == 'test-api-key'
        assert config.model_name == 'test-model'

    def test_load_from_environment_default_model(self):
        """Test loading configuration with default model when not specified."""
        config = Config()

        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-api-key'}):
            config.load_from_environment()

        assert config.api_key == 'test-api-key'
        assert config.model_name == "gemini-2.0-flash"

    def test_validate_missing_api_key(self):
        """Test validation fails when API key is missing."""
        config = Config()

        with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is required"):
            config.validate()

    def test_validate_with_api_key(self):
        """Test validation succeeds when API key is present."""
        config = Config()
        config.api_key = "test-api-key"

        # Should not raise an exception
        config.validate()

    def test_set_project_root_valid_path(self):
        """Test setting project root with valid path."""
        config = Config()

        with tempfile.TemporaryDirectory() as temp_dir:
            config.set_project_root(temp_dir)
            assert config.project_root == Path(temp_dir).resolve()

    def test_set_project_root_invalid_path(self):
        """Test setting project root with invalid path."""
        config = Config()

        with pytest.raises(ValueError, match="Project path is not a valid directory"):
            config.set_project_root("/nonexistent/path")

    def test_set_project_root_file_path(self):
        """Test setting project root with file path instead of directory."""
        config = Config()

        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(ValueError, match="Project path is not a valid directory"):
                config.set_project_root(temp_file.name)

    def test_set_output_dir_specified(self):
        """Test setting output directory when specified."""
        config = Config()

        with tempfile.TemporaryDirectory() as temp_dir:
            config.set_output_dir(temp_dir)
            assert config.output_dir == Path(temp_dir).resolve()

    def test_set_output_dir_none(self):
        """Test setting output directory to None."""
        config = Config()

        with tempfile.TemporaryDirectory() as temp_dir:
            config.project_root = Path(temp_dir)
            config.set_output_dir(None)
            assert config.output_dir == Path(temp_dir)

    def test_get_documentation_path_no_output_dir(self):
        """Test getting documentation path when no output dir is set."""
        config = Config()

        module_path = Path("/test/project/module.py")
        doc_path = config.get_documentation_path(module_path)

        assert doc_path == module_path

    def test_get_documentation_path_with_output_dir(self):
        """Test getting documentation path when output dir is set."""
        config = Config()

        config.project_root = Path("/test/project")
        config.output_dir = Path("/test/output")

        module_path = Path("/test/project/subdir/module.py")
        doc_path = config.get_documentation_path(module_path)

        expected_path = Path("/test/output/subdir/module.py")
        assert doc_path == expected_path
