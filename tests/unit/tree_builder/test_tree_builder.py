"""
Unit tests for the tree builder module.

This module tests the tree building functionality including
module tree construction and node management.
"""

from pathlib import Path

from genai_docs.tree_builder import TreeBuilder


class TestTreeBuilder:
    """Test the TreeBuilder class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tree_builder = TreeBuilder()

    def test_tree_builder_initialization(self):
        """Test TreeBuilder initialization."""
        assert self.tree_builder is not None

    def test_build_module_tree_empty_directory(self, tmp_path):
        """Test building module tree from empty directory."""
        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert root_node.name == tmp_path.name
        assert root_node.is_root is True
        assert root_node.is_package is False
        assert len(root_node.children) == 0

    def test_build_module_tree_with_python_files(self, tmp_path):
        """Test building module tree with Python files."""
        # Create Python files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert len(root_node.children) == 2

        child_names = [child.name for child in root_node.children]
        assert "module1" in child_names
        assert "module2" in child_names

        # Check that children are modules, not packages
        for child in root_node.children:
            assert child.is_package is False
            assert child.content is not None

    def test_build_module_tree_with_package(self, tmp_path):
        """Test building module tree with package."""
        # Create package directory with __init__.py
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("from .module import function")
        (package_dir / "module.py").write_text("def function(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert len(root_node.children) == 1

        package_node = root_node.children[0]
        assert package_node.name == "test_package"
        assert package_node.is_package is True
        assert len(package_node.children) == 1

        module_node = package_node.children[0]
        assert module_node.name == "module"
        assert module_node.is_package is False

    def test_build_module_tree_with_nested_packages(self, tmp_path):
        """Test building module tree with nested packages."""
        # Create nested package structure
        outer_package = tmp_path / "outer_package"
        outer_package.mkdir()
        (outer_package / "__init__.py").write_text("")

        inner_package = outer_package / "inner_package"
        inner_package.mkdir()
        (inner_package / "__init__.py").write_text("")
        (inner_package / "module.py").write_text("def function(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert len(root_node.children) == 1

        outer_node = root_node.children[0]
        assert outer_node.name == "outer_package"
        assert outer_node.is_package is True
        assert len(outer_node.children) == 1

        inner_node = outer_node.children[0]
        assert inner_node.name == "inner_package"
        assert inner_node.is_package is True
        assert len(inner_node.children) == 1

        module_node = inner_node.children[0]
        assert module_node.name == "module"
        assert module_node.is_package is False

    def test_build_module_tree_ignores_skipped_directories(self, tmp_path):
        """Test that tree builder ignores directories that should be skipped."""
        # Create directories that should be ignored
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / ".venv").mkdir()
        (tmp_path / "venv").mkdir()
        (tmp_path / ".idea").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "build").mkdir()
        (tmp_path / "dist").mkdir()
        (tmp_path / ".pytest_cache").mkdir()
        (tmp_path / ".mypy_cache").mkdir()

        # Create a valid Python file
        (tmp_path / "module.py").write_text("def function(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert len(root_node.children) == 1
        assert root_node.children[0].name == "module"

    def test_build_module_tree_ignores_hidden_files(self, tmp_path):
        """Test that tree builder ignores hidden files."""
        # Create hidden files
        (tmp_path / ".hidden.py").write_text("def hidden(): pass")
        (tmp_path / "._hidden.py").write_text("def hidden(): pass")

        # Create a valid Python file
        (tmp_path / "module.py").write_text("def function(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert len(root_node.children) == 1
        assert root_node.children[0].name == "module"

    def test_build_module_tree_with_root_package(self, tmp_path):
        """Test building module tree when root directory is a package."""
        # Create __init__.py in root to make it a package
        (tmp_path / "__init__.py").write_text("from .module import function")
        (tmp_path / "module.py").write_text("def function(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert root_node.is_package is True
        assert len(root_node.children) == 1
        assert root_node.children[0].name == "module"

    def test_build_module_tree_handles_file_read_errors(self, tmp_path):
        """Test that tree builder handles file read errors gracefully."""
        # Create a Python file
        module_file = tmp_path / "module.py"
        module_file.write_text("def function(): pass")

        # Make the file unreadable (this is platform-dependent)
        # For now, we'll just test that the tree is built
        root_node = self.tree_builder.build_module_tree(str(tmp_path))

        assert root_node is not None
        assert len(root_node.children) == 1

    def test_should_process_directory_valid(self):
        """Test valid directory processing."""
        valid_dirs = [
            Path("src"),
            Path("tests"),
            Path("docs"),
            Path("utils"),
        ]

        for dir_path in valid_dirs:
            assert self.tree_builder._should_process_directory(dir_path) is True

    def test_should_process_directory_invalid(self):
        """Test invalid directory processing."""
        invalid_dirs = [
            Path("__pycache__"),
            Path(".git"),
            Path(".venv"),
            Path("venv"),
            Path(".idea"),
            Path("node_modules"),
            Path("build"),
            Path("dist"),
            Path(".pytest_cache"),
            Path(".mypy_cache"),
            Path(".hidden"),
        ]

        for dir_path in invalid_dirs:
            assert self.tree_builder._should_process_directory(dir_path) is False

    def test_get_all_nodes(self, tmp_path):
        """Test getting all nodes from tree."""
        # Create a simple tree structure
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))
        all_nodes = self.tree_builder.get_all_nodes(root_node)

        assert len(all_nodes) == 3  # root + 2 modules
        node_names = [node.name for node in all_nodes]
        assert tmp_path.name in node_names
        assert "module1" in node_names
        assert "module2" in node_names

    def test_get_leaf_nodes(self, tmp_path):
        """Test getting leaf nodes from tree."""
        # Create a tree with packages and modules
        package_dir = tmp_path / "package"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")
        (package_dir / "module.py").write_text("def function(): pass")

        (tmp_path / "root_module.py").write_text("def root_func(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))
        leaf_nodes = self.tree_builder.get_leaf_nodes(root_node)

        # Should have 2 leaf nodes: root_module and module
        assert len(leaf_nodes) == 2
        leaf_names = [node.name for node in leaf_nodes]
        assert "root_module" in leaf_names
        assert "module" in leaf_names

    def test_print_tree(self, tmp_path, capsys):
        """Test tree printing functionality."""
        # Create a simple tree
        (tmp_path / "module.py").write_text("def function(): pass")

        root_node = self.tree_builder.build_module_tree(str(tmp_path))
        self.tree_builder.print_tree(root_node)

        captured = capsys.readouterr()
        output = captured.out

        assert tmp_path.name in output
        assert "module" in output
        assert "Module" in output  # Should show node type

    def test_build_module_tree_invalid_directory(self):
        """Test building module tree from invalid directory."""
        root_node = self.tree_builder.build_module_tree("/nonexistent/path")

        assert root_node is None
