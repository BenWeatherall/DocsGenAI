"""
Integration tests for the complete documentation workflow.

This module tests the end-to-end documentation generation process
using the new modular architecture.
"""

from unittest.mock import patch

import pytest

from genai_docs.config import config
from genai_docs.documentation_generator import doc_generator
from genai_docs.file_manager import file_manager
from genai_docs.tree_builder import tree_builder


class TestDocumentationWorkflow:
    """Test the complete documentation generation workflow."""

    def setup_method(self):
        """Setup test fixtures."""
        # Reset global instances for clean testing
        config.api_key = "test-api-key"
        config.model_name = "test-model"

    def create_test_project(self, tmp_path):
        """Create a test project structure."""
        # Create project files
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
description = "A test project"
""")

        (tmp_path / "README.md").write_text("# Test Project\n\nA test project for documentation generation.")

        # Create main package
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("""
from .core import CoreClass
from .utils import helper_function

__all__ = ['CoreClass', 'helper_function']
""")

        # Create core module
        (package_dir / "core.py").write_text("""
from .utils import helper_function

class CoreClass:
    def __init__(self):
        self.helper = helper_function()

    def process_data(self, data):
        return self.helper(data)
""")

        # Create utils module
        (package_dir / "utils.py").write_text("""
import json

def helper_function(data):
    return json.dumps(data)
""")

        # Create standalone module
        (tmp_path / "standalone.py").write_text("""
def standalone_function():
    return "I work independently"
""")

    @patch('genai_docs.llm_client.genai')
    def test_complete_documentation_workflow(self, mock_genai, tmp_path):
        """Test the complete documentation generation workflow."""
        # Create test project
        self.create_test_project(tmp_path)

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Generated documentation'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Build module tree
        root_node = tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert root_node.name == tmp_path.name
        assert root_node.is_root is True

        # Verify tree structure
        all_nodes = tree_builder.get_all_nodes(root_node)
        assert len(all_nodes) == 5  # root + package + 3 modules

        # Check package structure
        package_node = None
        for node in root_node.children:
            if node.name == "test_package":
                package_node = node
                break

        assert package_node is not None
        assert package_node.is_package is True
        assert len(package_node.children) == 2  # core.py and utils.py

        # Read project files
        project_files = file_manager.read_project_files(str(tmp_path))

        assert "pyproject.toml" in project_files
        assert "README.md" in project_files

        # Generate documentation
        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Verify documentation was generated
        assert root_node.documentation is not None
        assert root_node.processed is True

        # Verify package documentation
        assert package_node.documentation is not None
        assert package_node.processed is True

        # Verify module documentation
        for child in package_node.children:
            assert child.documentation is not None
            assert child.processed is True

    @patch('genai_docs.llm_client.genai')
    def test_documentation_with_dependencies(self, mock_genai, tmp_path):
        """Test documentation generation with module dependencies."""
        # Create a project with dependencies
        (tmp_path / "main.py").write_text("""
from .utils import helper
from .models import User

def main():
    user = User()
    return helper(user)
""")

        (tmp_path / "utils.py").write_text("""
def helper(obj):
    return str(obj)
""")

        (tmp_path / "models.py").write_text("""
from .utils import helper

class User:
    def __init__(self):
        self.name = "Test User"

    def __str__(self):
        return helper(self.name)
""")

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Generated documentation'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Build and document
        root_node = tree_builder.build_module_tree(str(tmp_path))
        project_files = file_manager.read_project_files(str(tmp_path))

        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Verify all modules were documented
        for child in root_node.children:
            assert child.documentation is not None
            assert child.processed is True

    @patch('genai_docs.llm_client.genai')
    def test_documentation_validation(self, mock_genai, tmp_path):
        """Test documentation validation functionality."""
        # Create test project
        self.create_test_project(tmp_path)

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Comprehensive documentation with lots of details'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Build and document
        root_node = tree_builder.build_module_tree(str(tmp_path))
        project_files = file_manager.read_project_files(str(tmp_path))

        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Validate documentation
        validation = doc_generator.validate_documentation(root_node)

        assert validation['valid'] is True
        assert validation['stats']['total_nodes'] > 0
        assert validation['stats']['documented_nodes'] > 0
        assert validation['stats']['failed_nodes'] == 0

    @patch('genai_docs.llm_client.genai')
    def test_documentation_summary_generation(self, mock_genai, tmp_path):
        """Test documentation summary generation."""
        # Create test project
        self.create_test_project(tmp_path)

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Generated documentation'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Build and document
        root_node = tree_builder.build_module_tree(str(tmp_path))
        project_files = file_manager.read_project_files(str(tmp_path))

        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Generate summary
        summary = doc_generator.get_documentation_summary(root_node)

        assert summary is not None
        assert len(summary) > 0
        assert "test_package" in summary
        assert "core" in summary
        assert "utils" in summary
        assert "standalone" in summary

    @patch('genai_docs.llm_client.genai')
    def test_file_manager_integration(self, mock_genai, tmp_path):
        """Test file manager integration with documentation workflow."""
        # Create test project
        self.create_test_project(tmp_path)

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Generated documentation'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Build and document
        root_node = tree_builder.build_module_tree(str(tmp_path))
        project_files = file_manager.read_project_files(str(tmp_path))

        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Test file manager functionality
        python_files = file_manager.find_python_files(tmp_path)
        assert len(python_files) > 0

        # Verify that all Python files were found
        file_names = [f.name for f in python_files]
        assert "core.py" in file_names
        assert "utils.py" in file_names
        assert "standalone.py" in file_names
        assert "__init__.py" in file_names

    @patch('genai_docs.llm_client.genai')
    def test_config_integration(self, mock_genai, tmp_path):
        """Test configuration integration with documentation workflow."""
        # Create test project
        self.create_test_project(tmp_path)

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Generated documentation'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Set configuration
        config.set_project_root(str(tmp_path))
        config.set_output_dir(str(tmp_path / "docs"))

        # Build and document
        root_node = tree_builder.build_module_tree(str(tmp_path))
        project_files = file_manager.read_project_files(str(tmp_path))

        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Verify configuration was used
        assert config.project_root == tmp_path
        assert config.output_dir == tmp_path / "docs"

    def test_error_handling_integration(self, tmp_path):
        """Test error handling in the documentation workflow."""
        # Create a project with invalid Python syntax
        (tmp_path / "invalid.py").write_text("""
def invalid_syntax(
    # Missing closing parenthesis
""")

        # Build module tree (should handle syntax errors gracefully)
        root_node = tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        # The invalid file should still be included in the tree
        assert len(root_node.children) == 1

        # Test with missing API key
        config.api_key = None

        with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is required"):
            config.validate()

    @patch('genai_docs.llm_client.genai')
    def test_performance_integration(self, mock_genai, tmp_path):
        """Test performance aspects of the documentation workflow."""
        # Create a larger test project
        for i in range(10):
            module_file = tmp_path / f"module_{i}.py"
            module_file.write_text(f"""
def function_{i}():
    return {i}
""")

        # Mock LLM responses
        mock_response = type('MockResponse', (), {
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': 'Generated documentation'})()]
                })()
            })()]
        })()

        mock_model = type('MockModel', (), {
            'generate_content': lambda x: mock_response
        })()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        # Build and document
        root_node = tree_builder.build_module_tree(str(tmp_path))
        project_files = file_manager.read_project_files(str(tmp_path))

        doc_generator.document_module_tree_bottom_up(root_node, project_files)

        # Verify all modules were processed
        assert len(root_node.children) == 10
        for child in root_node.children:
            assert child.processed is True
            assert child.documentation is not None
