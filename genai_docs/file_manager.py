"""
File management utilities for GenAI Docs.

This module handles all file I/O operations including reading project files,
saving documentation, and managing file paths.
"""

import logging
from pathlib import Path
from typing import Optional

from .config import config
from .core_types import ModuleNode

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for the documentation generator."""

    def __init__(self):
        """Initialize the file manager."""
        self.project_files_cache: dict[str, str] = {}

    def read_project_files(self, project_path: str) -> dict[str, str]:
        """
        Read project-level files that provide context for the overall project.

        Args:
            project_path: Path to the project root

        Returns:
            Dictionary containing project file contents
        """
        project_files = {}

        # Common project files to read
        files_to_read = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "README.md",
            "README.rst",
            "requirements.txt",
            "requirements-dev.txt",
            "Pipfile",
            "poetry.lock",
        ]

        for filename in files_to_read:
            file_path = Path(project_path) / filename
            if file_path.exists():
                try:
                    with file_path.open(encoding="utf-8") as f:
                        project_files[filename] = f.read()
                    logger.debug(f"Read project file: {filename}")
                except OSError as e:
                    logger.warning(f"Could not read {filename}: {e}")
                    project_files[filename] = f"# Error reading file: {e}"

        self.project_files_cache = project_files
        return project_files

    def read_module_content(self, module_path: Path) -> Optional[str]:
        """
        Read the content of a Python module file.

        Args:
            module_path: Path to the module file

        Returns:
            File content as string, or None if file cannot be read
        """
        try:
            with module_path.open(encoding="utf-8") as f:
                content = f.read()
            logger.debug(f"Read module content: {module_path}")
            return content
        except OSError as e:
            logger.warning(f"Could not read module file {module_path}: {e}")
            return None

    def read_init_file(self, package_path: Path) -> Optional[str]:
        """
        Read the __init__.py file of a package.

        Args:
            package_path: Path to the package directory

        Returns:
            __init__.py content as string, or None if file cannot be read
        """
        init_file_path = package_path / "__init__.py"
        if init_file_path.exists():
            return self.read_module_content(init_file_path)
        return None

    def save_documentation(self, node: ModuleNode, documentation: str) -> bool:
        """
        Save the generated documentation to a markdown file in the module's directory.
        Handles multiple nodes in the same directory by using appropriate filenames.

        Args:
            node: The ModuleNode containing the module/package
            documentation: The generated documentation text

        Returns:
            True if documentation was saved successfully, False otherwise
        """
        if not documentation or documentation.startswith("Error:"):
            logger.warning(f"No valid documentation to save for {node.name}")
            return False

        # Determine the appropriate filename based on node type and context
        if node.is_package:
            # For packages, use the standard DOCUMENTATION.md filename
            doc_filename = "DOCUMENTATION.md"
        else:
            # For modules, check if the directory also contains a package (has __init__.py)
            # to avoid conflicts with package documentation
            dir_path = Path(node.path).parent
            if (dir_path / "__init__.py").exists():
                # This directory is also a package, so use a module-specific filename
                doc_filename = f"{node.name}_DOCUMENTATION.md"
            else:
                # Check if there are multiple .py files in this directory
                py_files = [
                    f.name
                    for f in dir_path.iterdir()
                    if f.name.endswith(".py") and f.name != "__init__.py"
                ]
                if len(py_files) > 1:
                    # Multiple modules in this directory, use module-specific filename
                    doc_filename = f"{node.name}_DOCUMENTATION.md"
                else:
                    # Single module in this directory, safe to use standard name
                    doc_filename = "DOCUMENTATION.md"

        # Get the appropriate documentation path
        module_path = Path(node.path)
        if node.is_package:
            doc_path = config.get_documentation_path(module_path) / doc_filename
        else:
            doc_path = config.get_documentation_path(module_path.parent) / doc_filename

        try:
            # Ensure the directory exists
            doc_path.parent.mkdir(parents=True, exist_ok=True)

            with doc_path.open("w", encoding="utf-8") as f:
                f.write(f"# {node.name} Documentation\n\n")
                f.write(documentation)
            logger.info(f"Saved documentation to: {doc_path}")
            return True
        except OSError as e:
            logger.error(f"Error saving documentation for {node.name}: {e}")
            return False

    def get_module_file_path(self, node: ModuleNode) -> Path:
        """
        Get the file path for a module node.

        Args:
            node: The ModuleNode

        Returns:
            Path to the module file
        """
        if node.is_package:
            return Path(node.path) / "__init__.py"
        return Path(node.path)

    def is_valid_python_file(self, file_path: Path) -> bool:
        """
        Check if a file is a valid Python file to process.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be processed
        """
        # Skip common non-source files and hidden files
        skip_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".idea",
            ".DS_Store",
            "node_modules",
            "build",
            "dist",
            ".pytest_cache",
            ".mypy_cache",
        ]

        if file_path.name in skip_patterns:
            return False

        if file_path.name.startswith("."):
            return False

        return file_path.suffix == ".py"

    def find_python_files(self, directory: Path) -> list[Path]:
        """
        Find all Python files in a directory recursively.

        Args:
            directory: Directory to search

        Returns:
            List of Python file paths
        """
        python_files = []

        for item in directory.rglob("*.py"):
            if self.is_valid_python_file(item):
                python_files.append(item)

        return python_files


# Global file manager instance
file_manager = FileManager()
