"""
Unit tests for the file manager module.

This module tests the file management functionality including
reading project files, saving documentation, and file path management.
"""

from pathlib import Path

from genai_docs.core_types import ModuleNode
from genai_docs.file_manager import FileManager


class TestFileManager:
    """Test the FileManager class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.file_manager = FileManager()
        # Import config here to avoid circular imports
        from genai_docs.config import config
        self.config = config

    def test_file_manager_initialization(self):
        """Test FileManager initialization."""
        assert self.file_manager.project_files_cache == {}

    def test_read_project_files_empty_directory(self, tmp_path):
        """Test reading project files from empty directory."""
        project_files = self.file_manager.read_project_files(str(tmp_path))

        assert isinstance(project_files, dict)
        assert len(project_files) == 0

    def test_read_project_files_with_pyproject_toml(self, tmp_path):
        """Test reading project files with pyproject.toml present."""
        pyproject_content = "[project]\nname = 'test-project'"
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)

        project_files = self.file_manager.read_project_files(str(tmp_path))

        assert "pyproject.toml" in project_files
        assert project_files["pyproject.toml"] == pyproject_content

    def test_read_project_files_with_readme(self, tmp_path):
        """Test reading project files with README.md present."""
        readme_content = "# Test Project\n\nThis is a test project."
        readme_file = tmp_path / "README.md"
        readme_file.write_text(readme_content)

        project_files = self.file_manager.read_project_files(str(tmp_path))

        assert "README.md" in project_files
        assert project_files["README.md"] == readme_content

    def test_read_project_files_multiple_files(self, tmp_path):
        """Test reading multiple project files."""
        # Create multiple project files
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        (tmp_path / "README.md").write_text("# Test")
        (tmp_path / "requirements.txt").write_text("pytest\n")

        project_files = self.file_manager.read_project_files(str(tmp_path))

        assert len(project_files) == 3
        assert "pyproject.toml" in project_files
        assert "README.md" in project_files
        assert "requirements.txt" in project_files

    def test_read_module_content_success(self, tmp_path):
        """Test successfully reading module content."""
        module_content = "def test_function():\n    return True"
        module_file = tmp_path / "test_module.py"
        module_file.write_text(module_content)

        content = self.file_manager.read_module_content(module_file)

        assert content == module_content

    def test_read_module_content_file_not_found(self, tmp_path):
        """Test reading module content from non-existent file."""
        non_existent_file = tmp_path / "nonexistent.py"

        content = self.file_manager.read_module_content(non_existent_file)

        assert content is None

    def test_read_init_file_exists(self, tmp_path):
        """Test reading __init__.py file when it exists."""
        init_content = "from .module import function"
        init_file = tmp_path / "__init__.py"
        init_file.write_text(init_content)

        content = self.file_manager.read_init_file(tmp_path)

        assert content == init_content

    def test_read_init_file_not_exists(self, tmp_path):
        """Test reading __init__.py file when it doesn't exist."""
        content = self.file_manager.read_init_file(tmp_path)

        assert content is None

    def test_get_module_file_path_package(self):
        """Test getting file path for package node."""
        node = ModuleNode(
            path="/test/package",
            name="package",
            is_package=True
        )

        file_path = self.file_manager.get_module_file_path(node)

        assert file_path == Path("/test/package/__init__.py")

    def test_get_module_file_path_module(self):
        """Test getting file path for module node."""
        node = ModuleNode(
            path="/test/module.py",
            name="module",
            is_package=False
        )

        file_path = self.file_manager.get_module_file_path(node)

        assert file_path == Path("/test/module.py")

    def test_is_valid_python_file_valid(self):
        """Test valid Python file detection."""
        valid_files = [
            Path("module.py"),
            Path("test_module.py"),
            Path("_private_module.py"),
        ]

        for file_path in valid_files:
            assert self.file_manager.is_valid_python_file(file_path) is True

    def test_is_valid_python_file_invalid(self):
        """Test invalid Python file detection."""
        invalid_files = [
            Path("__pycache__"),
            Path(".git"),
            Path(".venv"),
            Path("venv"),
            Path(".idea"),
            Path(".DS_Store"),
            Path("node_modules"),
            Path("build"),
            Path("dist"),
            Path(".pytest_cache"),
            Path(".mypy_cache"),
            Path(".hidden.py"),
            Path("module.txt"),
            Path("module.pyc"),
        ]

        for file_path in invalid_files:
            assert self.file_manager.is_valid_python_file(file_path) is False

    def test_find_python_files(self, tmp_path):
        """Test finding Python files in directory."""
        # Create Python files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "module3.py").write_text("def func3(): pass")

        # Create non-Python files
        (tmp_path / "readme.txt").write_text("README")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "module1.pyc").write_text("compiled")

        python_files = self.file_manager.find_python_files(tmp_path)

        # Should find 3 Python files
        assert len(python_files) == 3
        file_names = [f.name for f in python_files]
        assert "module1.py" in file_names
        assert "module2.py" in file_names
        assert "module3.py" in file_names

    def test_save_documentation_package(self, tmp_path):
        """Test saving documentation for package."""
        # Set up config for this test
        self.config.set_project_root(str(tmp_path))

        node = ModuleNode(
            path=str(tmp_path),
            name="test_package",
            is_package=True
        )

        documentation = "# Test Package\n\nThis is a test package."

        success = self.file_manager.save_documentation(node, documentation)

        assert success is True
        doc_file = tmp_path / "DOCUMENTATION.md"
        assert doc_file.exists()
        assert doc_file.read_text().startswith("# test_package Documentation")

    def test_save_documentation_module(self, tmp_path):
        """Test saving documentation for module."""
        # Set up config for this test
        self.config.set_project_root(str(tmp_path))

        node = ModuleNode(
            path=str(tmp_path / "test_module.py"),
            name="test_module",
            is_package=False
        )

        documentation = "# Test Module\n\nThis is a test module."

        success = self.file_manager.save_documentation(node, documentation)

        assert success is True
        doc_file = tmp_path / "DOCUMENTATION.md"
        assert doc_file.exists()
        assert doc_file.read_text().startswith("# test_module Documentation")

    def test_save_documentation_error_content(self, tmp_path):
        """Test saving documentation with error content."""
        node = ModuleNode(
            path=str(tmp_path),
            name="test_package",
            is_package=True
        )

        # Test with None documentation
        success = self.file_manager.save_documentation(node, None)
        assert success is False

        # Test with error documentation
        success = self.file_manager.save_documentation(node, "Error: Something went wrong")
        assert success is False

    def test_save_documentation_module_with_package_conflict(self, tmp_path):
        """Test saving documentation for module when package exists in same directory."""
        # Set up config for this test
        self.config.set_project_root(str(tmp_path))

        # Create __init__.py to make it a package
        (tmp_path / "__init__.py").write_text("")

        node = ModuleNode(
            path=str(tmp_path / "test_module.py"),
            name="test_module",
            is_package=False
        )

        documentation = "# Test Module\n\nThis is a test module."

        success = self.file_manager.save_documentation(node, documentation)

        assert success is True
        # Should use module-specific filename
        doc_file = tmp_path / "test_module_DOCUMENTATION.md"
        assert doc_file.exists()

    def test_save_documentation_multiple_modules_same_dir(self, tmp_path):
        """Test saving documentation for multiple modules in same directory."""
        # Set up config for this test
        self.config.set_project_root(str(tmp_path))

        # Create multiple Python files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")

        node = ModuleNode(
            path=str(tmp_path / "module1.py"),
            name="module1",
            is_package=False
        )

        documentation = "# Test Module\n\nThis is a test module."

        success = self.file_manager.save_documentation(node, documentation)

        assert success is True
        # Should use module-specific filename due to multiple modules
        doc_file = tmp_path / "module1_DOCUMENTATION.md"
        assert doc_file.exists()
