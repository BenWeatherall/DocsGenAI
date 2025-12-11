"""
Unit tests for the CLI module.

This module tests the command-line interface functionality including
argument parsing and CLI workflow.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

from genai_docs.cli import create_parser, main, setup_logging, validate_project_path


class TestCLI:
    """Test the CLI functionality."""

    def test_create_parser(self):
        """Test argument parser creation."""
        parser = create_parser()

        assert parser is not None
        assert parser.description is not None
        assert "project_path" in [action.dest for action in parser._actions]

    def test_create_parser_arguments(self):
        """Test that all expected arguments are present."""
        parser = create_parser()

        # Get all argument names
        arg_names = [action.dest for action in parser._actions]

        # Check required arguments
        assert "project_path" in arg_names

        # Check optional arguments
        assert "output" in arg_names
        assert "verbose" in arg_names
        assert "dry_run" in arg_names
        assert "model" in arg_names
        assert "version" in arg_names

    def test_create_parser_help(self):
        """Test parser help text."""
        parser = create_parser()

        help_text = parser.format_help()
        assert "Generate comprehensive documentation" in help_text
        assert "Examples:" in help_text
        assert "genai-docs /path/to/project" in help_text

    def test_validate_project_path_valid(self, tmp_path):
        """Test project path validation with valid path."""
        assert validate_project_path(str(tmp_path)) is True

    def test_validate_project_path_nonexistent(self):
        """Test project path validation with nonexistent path."""
        assert validate_project_path("/nonexistent/path") is False

    def test_validate_project_path_file(self, tmp_path):
        """Test project path validation with file path."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        assert validate_project_path(str(file_path)) is False

    @patch("genai_docs.cli.logging.basicConfig")
    def test_setup_logging_info_level(self, mock_basic_config):
        """Test logging setup with info level."""
        setup_logging(verbose=False)

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == 20  # INFO level

    @patch("genai_docs.cli.logging.basicConfig")
    def test_setup_logging_debug_level(self, mock_basic_config):
        """Test logging setup with debug level."""
        setup_logging(verbose=True)

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == 10  # DEBUG level

    @patch("genai_docs.cli.LLMClient")
    @patch("genai_docs.cli.DocumentationCache")
    @patch("genai_docs.cli.config")
    @patch("genai_docs.cli.setup_logging")
    @patch("genai_docs.cli.validate_project_path")
    @patch("genai_docs.cli.build_and_validate_tree")
    @patch("genai_docs.cli.generate_documentation")
    @patch("genai_docs.cli.print_summary")
    @patch("genai_docs.cli.validate_results")
    def test_main_success(
        self,
        mock_validate_results,
        mock_print_summary,
        mock_generate_doc,
        mock_build_tree,
        mock_validate_path,
        mock_setup_logging,
        mock_config,
        mock_cache_class,
        mock_llm_client_class,
    ):
        """Test successful main execution."""
        # Mock all dependencies
        mock_config.load_from_environment.return_value = None
        mock_config.validate.return_value = None
        mock_config.set_project_root.return_value = None
        mock_config.set_output_dir.return_value = None
        # Set config attributes that are accessed in main()
        mock_config.force_regenerate = False
        mock_config.use_cache = True
        mock_config.use_dependency_graph = True
        mock_config.verbose = False
        mock_config.project_root = Path("/test/path")

        # Mock LLM client
        mock_llm_client = Mock()
        mock_llm_client_class.return_value = mock_llm_client

        # Mock cache
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache

        mock_validate_path.return_value = True

        mock_tree = Mock()
        mock_build_tree.return_value = mock_tree

        # Mock command line arguments
        with patch.object(sys, "argv", ["genai-docs", "/test/path"]):
            result = main()

        assert result == 0

        # Verify all functions were called
        mock_config.load_from_environment.assert_called_once()
        mock_config.validate.assert_called_once()
        mock_setup_logging.assert_called_once_with(verbose=False)
        mock_validate_path.assert_called_once_with("/test/path")
        mock_config.set_project_root.assert_called_once_with("/test/path")
        mock_llm_client_class.assert_called_once()
        mock_build_tree.assert_called_once_with("/test/path")
        # Note: doc_generator is now passed as a parameter, so we check it's in the call
        mock_generate_doc.assert_called_once()
        call_args = mock_generate_doc.call_args
        assert call_args[0][0] == mock_tree  # module_tree_root
        assert call_args[0][1] == "/test/path"  # project_path
        assert call_args[0][3] is False  # dry_run
        mock_print_summary.assert_called_once()
        call_args = mock_print_summary.call_args
        assert call_args[0][0] == mock_tree  # module_tree_root
        assert call_args[0][2] is False  # dry_run
        mock_validate_results.assert_called_once()
        call_args = mock_validate_results.call_args
        assert call_args[0][0] == mock_tree  # module_tree_root
        assert call_args[0][2] is False  # dry_run

    @patch("genai_docs.cli.LLMClient")
    @patch("genai_docs.cli.config")
    @patch("genai_docs.cli.setup_logging")
    def test_main_invalid_project_path(
        self, mock_setup_logging, mock_config, mock_llm_client_class
    ):
        """Test main execution with invalid project path."""
        # Mock dependencies
        mock_config.load_from_environment.return_value = None
        mock_config.validate.return_value = None

        # Mock command line arguments
        with patch.object(sys, "argv", ["genai-docs", "/nonexistent/path"]):
            with patch("genai_docs.cli.validate_project_path", return_value=False):
                result = main()

        assert result == 1

    @patch("genai_docs.cli.config")
    def test_main_config_validation_failure(self, mock_config):
        """Test main execution with config validation failure."""
        # Mock config to raise exception
        mock_config.load_from_environment.return_value = None
        mock_config.validate.side_effect = ValueError("Missing API key")

        # Mock command line arguments
        with patch.object(sys, "argv", ["genai-docs", "/test/path"]):
            result = main()

        assert result == 1

    @patch("genai_docs.cli.config")
    @patch("genai_docs.cli.setup_logging")
    @patch("genai_docs.cli.validate_project_path")
    def test_main_tree_building_failure(
        self, mock_validate_path, mock_setup_logging, mock_config
    ):
        """Test main execution with tree building failure."""
        # Mock dependencies
        mock_config.load_from_environment.return_value = None
        mock_config.validate.return_value = None
        mock_config.set_project_root.return_value = None

        mock_validate_path.return_value = True

        # Mock command line arguments
        with (
            patch.object(sys, "argv", ["genai-docs", "/test/path"]),
            patch(
                "genai_docs.cli.build_and_validate_tree",
                side_effect=ValueError("No modules found"),
            ),
        ):
            result = main()

        assert result == 1

    @patch("genai_docs.cli.LLMClient")
    @patch("genai_docs.cli.config")
    @patch("genai_docs.cli.setup_logging")
    @patch("genai_docs.cli.validate_project_path")
    @patch("genai_docs.cli.build_and_validate_tree")
    def test_main_keyboard_interrupt(
        self,
        mock_build_tree,
        mock_validate_path,
        mock_setup_logging,
        mock_config,
        mock_llm_client_class,
    ):
        """Test main execution with keyboard interrupt."""
        # Mock dependencies
        mock_config.load_from_environment.return_value = None
        mock_config.validate.return_value = None
        mock_config.set_project_root.return_value = None

        mock_validate_path.return_value = True
        mock_build_tree.side_effect = KeyboardInterrupt()

        # Mock command line arguments
        with patch.object(sys, "argv", ["genai-docs", "/test/path"]):
            result = main()

        assert result == 1

    @patch("genai_docs.cli.LLMClient")
    @patch("genai_docs.cli.config")
    @patch("genai_docs.cli.setup_logging")
    @patch("genai_docs.cli.validate_project_path")
    @patch("genai_docs.cli.build_and_validate_tree")
    @patch("genai_docs.cli.generate_documentation")
    @patch("genai_docs.cli.print_summary")
    @patch("genai_docs.cli.validate_results")
    def test_main_with_options(
        self,
        mock_validate_results,
        mock_print_summary,
        mock_generate_doc,
        mock_build_tree,
        mock_validate_path,
        mock_setup_logging,
        mock_config,
        mock_llm_client_class,
    ):
        """Test main execution with various options."""
        # Mock all dependencies
        mock_config.load_from_environment.return_value = None
        mock_config.validate.return_value = None
        mock_config.set_project_root.return_value = None
        mock_config.set_output_dir.return_value = None

        mock_validate_path.return_value = True

        mock_tree = Mock()
        mock_build_tree.return_value = mock_tree

        # Mock command line arguments with options
        with patch.object(
            sys,
            "argv",
            [
                "genai-docs",
                "/test/path",
                "--verbose",
                "--dry-run",
                "--output",
                "/output/path",
                "--model",
                "test-model",
            ],
        ):
            result = main()

        assert result == 0

        # Verify options were processed
        mock_setup_logging.assert_called_once_with(verbose=True)
        mock_config.set_output_dir.assert_called_once_with("/output/path")
        mock_llm_client_class.assert_called_once()
        # Note: doc_generator is now passed as a parameter
        mock_generate_doc.assert_called_once()
        call_args = mock_generate_doc.call_args
        assert call_args[0][0] == mock_tree  # module_tree_root
        assert call_args[0][1] == "/test/path"  # project_path
        assert call_args[0][3] is True  # dry_run=True
        mock_print_summary.assert_called_once()
        call_args = mock_print_summary.call_args
        assert call_args[0][0] == mock_tree  # module_tree_root
        assert call_args[0][2] is True  # dry_run=True
        mock_validate_results.assert_called_once()
        call_args = mock_validate_results.call_args
        assert call_args[0][0] == mock_tree  # module_tree_root
        assert call_args[0][2] is True  # dry_run=True

    @patch("genai_docs.cli.LLMClient")
    @patch("genai_docs.cli.config")
    def test_main_missing_api_key(self, mock_config, mock_llm_client_class):
        """Test main execution with missing API key."""
        # Mock config to simulate missing API key
        mock_config.load_from_environment.return_value = None
        mock_config.validate.side_effect = ValueError(
            "GOOGLE_API_KEY environment variable is required"
        )

        # Mock command line arguments
        with patch.object(sys, "argv", ["genai-docs", "/test/path"]):
            result = main()

        assert result == 1

    @patch("genai_docs.cli.LLMClient")
    @patch("genai_docs.cli.config")
    @patch("genai_docs.cli.setup_logging")
    @patch("genai_docs.cli.validate_project_path")
    @patch("genai_docs.cli.build_and_validate_tree")
    @patch("genai_docs.cli.generate_documentation")
    @patch("genai_docs.cli.print_summary")
    @patch("genai_docs.cli.validate_results")
    def test_main_general_exception(
        self,
        mock_validate_results,
        mock_print_summary,
        mock_generate_doc,
        mock_build_tree,
        mock_validate_path,
        mock_setup_logging,
        mock_config,
        mock_llm_client_class,
    ):
        """Test main execution with general exception."""
        # Mock all dependencies
        mock_config.load_from_environment.return_value = None
        mock_config.validate.return_value = None
        mock_config.set_project_root.return_value = None

        mock_validate_path.return_value = True
        mock_build_tree.side_effect = Exception("Unexpected error")

        # Mock command line arguments
        with patch.object(sys, "argv", ["genai-docs", "/test/path"]):
            result = main()

        assert result == 1
