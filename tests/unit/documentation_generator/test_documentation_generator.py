"""
Unit tests for the documentation generator module.

This module tests the documentation generation functionality including
bottom-up documentation process and validation.
"""

from unittest.mock import Mock, patch

import pytest

from genai_docs.core_types import ModuleNode
from genai_docs.documentation_generator import DocumentationGenerator
from genai_docs.exceptions import DocumentationError
from genai_docs.llm_client import LLMClient


class TestDocumentationGenerator:
    """Test the DocumentationGenerator class."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.doc_generator = DocumentationGenerator(llm_client=self.mock_llm_client)

    def test_documentation_generator_initialization(self) -> None:
        """Test DocumentationGenerator initialization."""
        assert self.doc_generator is not None

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_module_tree_bottom_up_leaf_module(self, mock_file_manager):
        """Test documenting a leaf module."""
        # Create a leaf module node
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False,
            content="def test_function(): pass",
        )

        # Mock LLM response
        self.mock_llm_client.generate_module_documentation.return_value = (
            "Module documentation"
        )
        mock_file_manager.save_documentation.return_value = True

        # Disable dependency graph for simple test
        result = self.doc_generator.document_module_tree_bottom_up(
            node, use_dependency_ordering=False
        )

        assert result == "Module documentation"
        assert node.documentation == "Module documentation"
        assert node.processed is True

        self.mock_llm_client.generate_module_documentation.assert_called_once()
        # Check that dependency_context is passed (may be empty dict)
        call_args = self.mock_llm_client.generate_module_documentation.call_args
        assert call_args[0][0] == "test_module"  # module_name
        assert call_args[0][1] == "def test_function(): pass"  # module_content
        mock_file_manager.save_documentation.assert_called_once_with(
            node, "Module documentation"
        )

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_module_tree_bottom_up_package(self, mock_file_manager):
        """Test documenting a package with children."""
        # Create child module
        child_node = ModuleNode(
            path="/test/package/child.py",
            name="child_module",
            is_package=False,
            content="def child_function(): pass",
        )

        # Create package node
        package_node = ModuleNode(
            path="/test/package", name="test_package", is_package=True
        )
        package_node.add_child(child_node)

        # Mock LLM responses
        self.mock_llm_client.generate_module_documentation.return_value = (
            "Child documentation"
        )
        self.mock_llm_client.generate_package_documentation.return_value = (
            "Package documentation"
        )
        mock_file_manager.save_documentation.return_value = True
        mock_file_manager.read_init_file.return_value = (
            "from .child import child_function"
        )

        # Disable dependency graph for simple test
        result = self.doc_generator.document_module_tree_bottom_up(
            package_node, use_dependency_ordering=False
        )

        assert result == "Package documentation"
        assert package_node.documentation == "Package documentation"
        assert package_node.processed is True
        assert child_node.documentation == "Child documentation"
        assert child_node.processed is True

        # Verify child was documented first (bottom-up)
        self.mock_llm_client.generate_module_documentation.assert_called_once()
        self.mock_llm_client.generate_package_documentation.assert_called_once()

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_module_tree_bottom_up_project_root(self, mock_file_manager):
        """Test documenting project root."""
        # Create project root node
        root_node = ModuleNode(path="/test/project", name="test_project", is_root=True)

        # Mock LLM response
        self.mock_llm_client.generate_project_documentation.return_value = (
            "Project documentation"
        )
        mock_file_manager.save_documentation.return_value = True

        project_files = {"pyproject.toml": "[project]\nname = 'test'"}

        # Disable dependency graph to use simple recursive method
        result = self.doc_generator.document_module_tree_bottom_up(
            root_node, project_files, use_dependency_ordering=False
        )

        assert result == "Project documentation"
        assert root_node.documentation == "Project documentation"
        assert root_node.processed is True

        self.mock_llm_client.generate_project_documentation.assert_called_once_with(
            project_files, []
        )

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_module_tree_bottom_up_already_processed(self, mock_file_manager):
        """Test that already processed nodes are not re-documented."""
        node = ModuleNode(path="/test/module.py", name="test_module", is_package=False)
        node.processed = True
        node.documentation = "Existing documentation"

        # Disable dependency graph for simple test
        result = self.doc_generator.document_module_tree_bottom_up(
            node, use_dependency_ordering=False
        )

        assert result == "Existing documentation"
        self.mock_llm_client.generate_module_documentation.assert_not_called()
        mock_file_manager.save_documentation.assert_not_called()

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_module_tree_bottom_up_save_failure(self, mock_file_manager):
        """Test handling of documentation save failure."""
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False,
            content="def test_function(): pass",
        )

        self.mock_llm_client.generate_module_documentation.return_value = (
            "Module documentation"
        )
        mock_file_manager.save_documentation.return_value = False

        # Disable dependency graph for simple test
        # Note: The new implementation raises DocumentationError on save failure
        with pytest.raises(DocumentationError):
            self.doc_generator.document_module_tree_bottom_up(
                node, use_dependency_ordering=False
            )

    def test_get_documentation_summary(self):
        """Test documentation summary generation."""
        # Create a simple tree
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="Project documentation",
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False,
            documentation="Module documentation",
        )
        root_node.add_child(child_node)

        summary = self.doc_generator.get_documentation_summary(root_node)

        assert "test_project" in summary
        assert "Project" in summary
        assert "Project documentation" in summary
        assert "test_module" in summary
        assert "Module" in summary
        assert "Module documentation" in summary

    def test_get_documentation_summary_no_documentation(self):
        """Test documentation summary for nodes without documentation."""
        root_node = ModuleNode(path="/test/project", name="test_project", is_root=True)

        child_node = ModuleNode(
            path="/test/project/module.py", name="test_module", is_package=False
        )
        root_node.add_child(child_node)

        summary = self.doc_generator.get_documentation_summary(root_node)

        assert "test_project" in summary
        assert "test_module" in summary
        assert "No documentation generated" in summary

    def test_validate_documentation_success(self):
        """Test documentation validation for successful case."""
        # Create nodes with good documentation
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="This is a comprehensive project documentation with lots of details about the project structure and functionality.",
            processed=True,
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False,
            documentation="This is a comprehensive module documentation with lots of details about the module functionality.",
            processed=True,
        )
        root_node.add_child(child_node)

        validation = self.doc_generator.validate_documentation(root_node)

        assert validation["valid"] is True
        assert validation["stats"]["total_nodes"] == 2
        assert validation["stats"]["documented_nodes"] == 2
        assert validation["stats"]["failed_nodes"] == 0
        assert validation["stats"]["empty_documentation"] == 0
        assert len(validation["issues"]) == 0
        assert len(validation["warnings"]) == 0

    def test_validate_documentation_with_issues(self):
        """Test documentation validation with issues."""
        # Create nodes with problems
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="Error: API call failed",
            processed=True,
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False,
            documentation="Short",  # Too short
            processed=True,
        )

        unprocessed_node = ModuleNode(
            path="/test/project/another.py",
            name="another_module",
            is_package=False,
            processed=False,
        )

        root_node.add_child(child_node)
        root_node.add_child(unprocessed_node)

        validation = self.doc_generator.validate_documentation(root_node)

        assert validation["valid"] is False
        assert validation["stats"]["total_nodes"] == 3
        assert validation["stats"]["documented_nodes"] == 0
        assert validation["stats"]["failed_nodes"] == 2
        assert validation["stats"]["empty_documentation"] == 1
        assert (
            len(validation["issues"]) == 2
        )  # Error in documentation + unprocessed node
        assert len(validation["warnings"]) == 1  # Short documentation

    def test_validate_documentation_empty_nodes(self):
        """Test documentation validation with empty nodes."""
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="",
            processed=True,
        )

        validation = self.doc_generator.validate_documentation(root_node)

        assert validation["valid"] is True  # No critical issues
        assert validation["stats"]["total_nodes"] == 1
        assert validation["stats"]["documented_nodes"] == 0
        assert validation["stats"]["failed_nodes"] == 0
        assert validation["stats"]["empty_documentation"] == 1
        assert len(validation["warnings"]) == 1  # Empty documentation warning

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_node_package(self, mock_file_manager):
        """Test _document_node for package."""
        node = ModuleNode(path="/test/package", name="test_package", is_package=True)

        self.mock_llm_client.generate_package_documentation.return_value = (
            "Package documentation"
        )
        mock_file_manager.read_init_file.return_value = "from .module import function"

        result = self.doc_generator._document_node(node)

        assert result == "Package documentation"
        self.mock_llm_client.generate_package_documentation.assert_called_once()

    def test_document_node_module(self):
        """Test _document_node for module."""
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False,
            content="def test_function(): pass",
        )

        self.mock_llm_client.generate_module_documentation.return_value = (
            "Module documentation"
        )

        result = self.doc_generator._document_node(node)

        assert result == "Module documentation"
        # Check that the method was called with correct arguments
        # Note: dependency_context may be passed as well
        call_args = self.mock_llm_client.generate_module_documentation.call_args
        assert call_args[0][0] == "test_module"  # module_name
        assert call_args[0][1] == "def test_function(): pass"  # module_content

    @patch("genai_docs.documentation_generator.file_manager")
    def test_document_project_root(self, mock_file_manager):
        """Test _document_project_root."""
        node = ModuleNode(path="/test/project", name="test_project", is_root=True)

        project_files = {"pyproject.toml": "[project]\nname = 'test'"}

        self.mock_llm_client.generate_project_documentation.return_value = (
            "Project documentation"
        )

        result = self.doc_generator._document_project_root(node, project_files)

        assert result == "Project documentation"
        self.mock_llm_client.generate_project_documentation.assert_called_once_with(
            project_files, []
        )
