"""
Unit tests for the documentation generator module.

This module tests the documentation generation functionality including
bottom-up documentation process and validation.
"""

from unittest.mock import patch

from genai_docs.core_types import ModuleNode
from genai_docs.documentation_generator import DocumentationGenerator


class TestDocumentationGenerator:
    """Test the DocumentationGenerator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.doc_generator = DocumentationGenerator()

    def test_documentation_generator_initialization(self):
        """Test DocumentationGenerator initialization."""
        assert self.doc_generator is not None

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_module_tree_bottom_up_leaf_module(self, mock_file_manager, mock_llm_client):
        """Test documenting a leaf module."""
        # Create a leaf module node
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False,
            content="def test_function(): pass"
        )

        # Mock LLM response
        mock_llm_client.generate_module_documentation.return_value = "Module documentation"
        mock_file_manager.save_documentation.return_value = True

        result = self.doc_generator.document_module_tree_bottom_up(node)

        assert result == "Module documentation"
        assert node.documentation == "Module documentation"
        assert node.processed is True

        mock_llm_client.generate_module_documentation.assert_called_once_with(
            "test_module", "def test_function(): pass"
        )
        mock_file_manager.save_documentation.assert_called_once_with(node, "Module documentation")

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_module_tree_bottom_up_package(self, mock_file_manager, mock_llm_client):
        """Test documenting a package with children."""
        # Create child module
        child_node = ModuleNode(
            path="/test/package/child.py",
            name="child_module",
            is_package=False,
            content="def child_function(): pass"
        )

        # Create package node
        package_node = ModuleNode(
            path="/test/package",
            name="test_package",
            is_package=True
        )
        package_node.add_child(child_node)

        # Mock LLM responses
        mock_llm_client.generate_module_documentation.return_value = "Child documentation"
        mock_llm_client.generate_package_documentation.return_value = "Package documentation"
        mock_file_manager.save_documentation.return_value = True
        mock_file_manager.read_init_file.return_value = "from .child import child_function"

        result = self.doc_generator.document_module_tree_bottom_up(package_node)

        assert result == "Package documentation"
        assert package_node.documentation == "Package documentation"
        assert package_node.processed is True
        assert child_node.documentation == "Child documentation"
        assert child_node.processed is True

        # Verify child was documented first (bottom-up)
        mock_llm_client.generate_module_documentation.assert_called_once()
        mock_llm_client.generate_package_documentation.assert_called_once()

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_module_tree_bottom_up_project_root(self, mock_file_manager, mock_llm_client):
        """Test documenting project root."""
        # Create project root node
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True
        )

        # Mock LLM response
        mock_llm_client.generate_project_documentation.return_value = "Project documentation"
        mock_file_manager.save_documentation.return_value = True

        project_files = {"pyproject.toml": "[project]\nname = 'test'"}

        result = self.doc_generator.document_module_tree_bottom_up(root_node, project_files)

        assert result == "Project documentation"
        assert root_node.documentation == "Project documentation"
        assert root_node.processed is True

        mock_llm_client.generate_project_documentation.assert_called_once_with(
            project_files, []
        )

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_module_tree_bottom_up_already_processed(self, mock_file_manager, mock_llm_client):
        """Test that already processed nodes are not re-documented."""
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False
        )
        node.processed = True
        node.documentation = "Existing documentation"

        result = self.doc_generator.document_module_tree_bottom_up(node)

        assert result == "Existing documentation"
        mock_llm_client.generate_module_documentation.assert_not_called()
        mock_file_manager.save_documentation.assert_not_called()

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_module_tree_bottom_up_save_failure(self, mock_file_manager, mock_llm_client):
        """Test handling of documentation save failure."""
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False,
            content="def test_function(): pass"
        )

        mock_llm_client.generate_module_documentation.return_value = "Module documentation"
        mock_file_manager.save_documentation.return_value = False

        result = self.doc_generator.document_module_tree_bottom_up(node)

        assert result == "Module documentation"
        assert node.documentation == "Module documentation"
        assert node.processed is False  # Should not be marked as processed if save failed

    def test_get_documentation_summary(self):
        """Test documentation summary generation."""
        # Create a simple tree
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="Project documentation"
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False,
            documentation="Module documentation"
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
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False
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
            processed=True
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False,
            documentation="This is a comprehensive module documentation with lots of details about the module functionality.",
            processed=True
        )
        root_node.add_child(child_node)

        validation = self.doc_generator.validate_documentation(root_node)

        assert validation['valid'] is True
        assert validation['stats']['total_nodes'] == 2
        assert validation['stats']['documented_nodes'] == 2
        assert validation['stats']['failed_nodes'] == 0
        assert validation['stats']['empty_documentation'] == 0
        assert len(validation['issues']) == 0
        assert len(validation['warnings']) == 0

    def test_validate_documentation_with_issues(self):
        """Test documentation validation with issues."""
        # Create nodes with problems
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="Error: API call failed",
            processed=True
        )

        child_node = ModuleNode(
            path="/test/project/module.py",
            name="test_module",
            is_package=False,
            documentation="Short",  # Too short
            processed=True
        )

        unprocessed_node = ModuleNode(
            path="/test/project/another.py",
            name="another_module",
            is_package=False,
            processed=False
        )

        root_node.add_child(child_node)
        root_node.add_child(unprocessed_node)

        validation = self.doc_generator.validate_documentation(root_node)

        assert validation['valid'] is False
        assert validation['stats']['total_nodes'] == 3
        assert validation['stats']['documented_nodes'] == 0
        assert validation['stats']['failed_nodes'] == 2
        assert validation['stats']['empty_documentation'] == 1
        assert len(validation['issues']) == 2  # Error in documentation + unprocessed node
        assert len(validation['warnings']) == 1  # Short documentation

    def test_validate_documentation_empty_nodes(self):
        """Test documentation validation with empty nodes."""
        root_node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True,
            documentation="",
            processed=True
        )

        validation = self.doc_generator.validate_documentation(root_node)

        assert validation['valid'] is True  # No critical issues
        assert validation['stats']['total_nodes'] == 1
        assert validation['stats']['documented_nodes'] == 0
        assert validation['stats']['failed_nodes'] == 0
        assert validation['stats']['empty_documentation'] == 1
        assert len(validation['warnings']) == 1  # Empty documentation warning

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_node_package(self, mock_file_manager, mock_llm_client):
        """Test _document_node for package."""
        node = ModuleNode(
            path="/test/package",
            name="test_package",
            is_package=True
        )

        mock_llm_client.generate_package_documentation.return_value = "Package documentation"
        mock_file_manager.read_init_file.return_value = "from .module import function"

        result = self.doc_generator._document_node(node)

        assert result == "Package documentation"
        mock_llm_client.generate_package_documentation.assert_called_once()

    @patch('genai_docs.documentation_generator.llm_client')
    def test_document_node_module(self, mock_llm_client):
        """Test _document_node for module."""
        node = ModuleNode(
            path="/test/module.py",
            name="test_module",
            is_package=False,
            content="def test_function(): pass"
        )

        mock_llm_client.generate_module_documentation.return_value = "Module documentation"

        result = self.doc_generator._document_node(node)

        assert result == "Module documentation"
        mock_llm_client.generate_module_documentation.assert_called_once_with(
            "test_module", "def test_function(): pass"
        )

    @patch('genai_docs.documentation_generator.llm_client')
    @patch('genai_docs.documentation_generator.file_manager')
    def test_document_project_root(self, mock_file_manager, mock_llm_client):
        """Test _document_project_root."""
        node = ModuleNode(
            path="/test/project",
            name="test_project",
            is_root=True
        )

        project_files = {"pyproject.toml": "[project]\nname = 'test'"}

        mock_llm_client.generate_project_documentation.return_value = "Project documentation"

        result = self.doc_generator._document_project_root(node, project_files)

        assert result == "Project documentation"
        mock_llm_client.generate_project_documentation.assert_called_once_with(
            project_files, []
        )
