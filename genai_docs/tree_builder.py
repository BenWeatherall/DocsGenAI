"""
Module tree building utilities for GenAI Docs.

This module handles the construction of hierarchical ModuleNode trees
from Python project directories.
"""

import logging
from pathlib import Path

from .core_types import ModuleNode
from .file_manager import file_manager

logger = logging.getLogger(__name__)


class TreeBuilder:
    """Builds hierarchical ModuleNode trees from Python project directories."""

    def __init__(self) -> None:
        """Initialize the tree builder."""

    def build_module_tree(self, root_dir: str) -> ModuleNode | None:
        """
        Recursively scans a given root directory to identify Python modules and packages,
        building a hierarchical ModuleNode tree.

        Args:
            root_dir: The absolute path to the root of the Python repository.

        Returns:
            The root node of the module tree, or None if the directory is invalid.
        """
        root_dir = Path(root_dir).resolve()
        if not root_dir.is_dir():
            logger.error(f"Directory not found: {root_dir}")
            return None

        # Determine the base name for the root module/package.
        # If the root_dir itself is a package, its name is the directory name.
        # Otherwise, it's a container for top-level modules/packages.
        root_name = root_dir.name
        is_root_package = (root_dir / "__init__.py").exists()

        # Create the root node for the tree.
        # If the root_dir is a package, it's a package node.
        # If it's just a directory containing modules, it's a conceptual root.
        root_node = ModuleNode(
            path=str(root_dir), name=root_name, is_package=is_root_package, is_root=True
        )

        # Start the recursive building process from the root directory
        self._build_recursive(root_dir, root_node)

        logger.info(f"Built module tree with root: {root_name}")
        return root_node

    def _build_recursive(self, current_path: Path, parent_node: ModuleNode) -> None:
        """
        Helper function to recursively traverse directories and build the module tree.

        Args:
            current_path: Current directory path to process
            parent_node: Parent ModuleNode to attach children to
        """
        for item in current_path.iterdir():
            item_name = item.name
            item_path = item

            # Skip files/directories that should be ignored
            if not file_manager.is_valid_python_file(
                item_path
            ) and not self._should_process_directory(item_path):
                continue

            if item_path.is_dir():
                # Check if it's a Python package (contains __init__.py)
                if (item_path / "__init__.py").exists():
                    module_name = item_name
                    node = ModuleNode(
                        path=str(item_path), name=module_name, is_package=True
                    )
                    parent_node.add_child(node)
                    logger.debug(f"Added package: {module_name}")
                    # Recursively build for the new package
                    self._build_recursive(item_path, node)
                else:
                    # It's a regular directory, recurse into it but attach children to the current parent.
                    # This handles cases where Python files are in subdirectories not marked as packages.
                    self._build_recursive(item_path, parent_node)
            elif item_path.is_file() and item_name.endswith(".py"):
                # It's a Python module file
                if item_name == "__init__.py":
                    # __init__.py content is handled when its parent directory is identified as a package.
                    # We don't create a separate node for __init__.py itself as a module.
                    continue
                module_name = item_name[:-3]  # Remove .py extension to get module name
                node = ModuleNode(
                    path=str(item_path), name=module_name, is_package=False
                )

                # Read the module content
                content = file_manager.read_module_content(item_path)
                if content is not None:
                    node.content = content
                else:
                    node.content = f"# Error reading file: {item_path}"

                parent_node.add_child(node)
                logger.debug(f"Added module: {module_name}")

    def _should_process_directory(self, dir_path: Path) -> bool:
        """
        Check if a directory should be processed for Python files.

        Args:
            dir_path: Directory path to check

        Returns:
            True if the directory should be processed
        """
        # Skip common non-source directories
        skip_dirs = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".idea",
            "node_modules",
            "build",
            "dist",
            ".pytest_cache",
            ".mypy_cache",
        }

        if dir_path.name in skip_dirs:
            return False

        return not dir_path.name.startswith(".")

    def get_all_nodes(self, root_node: ModuleNode) -> list[ModuleNode]:
        """
        Get all nodes in the tree recursively.

        Args:
            root_node: Root node of the tree

        Returns:
            List of all ModuleNode objects in the tree
        """
        nodes = [root_node]
        for child in root_node.children:
            nodes.extend(self.get_all_nodes(child))
        return nodes

    def get_leaf_nodes(self, root_node: ModuleNode) -> list[ModuleNode]:
        """
        Get all leaf nodes (nodes with no children) in the tree.

        Args:
            root_node: Root node of the tree

        Returns:
            List of leaf ModuleNode objects
        """
        if not root_node.children:
            return [root_node]

        leaf_nodes = []
        for child in root_node.children:
            leaf_nodes.extend(self.get_leaf_nodes(child))
        return leaf_nodes

    def print_tree(self, node: ModuleNode, level: int = 0) -> None:
        """
        Print a visual representation of the module tree.

        Args:
            node: Current node to print
            level: Current indentation level
        """
        indent = "  " * level
        node_type = (
            "Project" if node.is_root else ("Package" if node.is_package else "Module")
        )
        print(f"{indent}- {node.name} ({node_type})")

        for child in sorted(node.children, key=lambda c: c.name):
            self.print_tree(child, level + 1)


# Global tree builder instance
tree_builder = TreeBuilder()
