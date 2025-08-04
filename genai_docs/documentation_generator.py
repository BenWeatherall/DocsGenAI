"""
Documentation generation logic for GenAI Docs.

This module handles the bottom-up documentation generation process,
orchestrating the documentation of modules, packages, and projects.
"""

import logging
from pathlib import Path
from typing import Optional

from .core_types import ModuleNode
from .file_manager import file_manager
from .llm_client import llm_client

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Handles the documentation generation process."""

    def __init__(self):
        """Initialize the documentation generator."""

    def document_module_tree_bottom_up(self, node: ModuleNode,
                                     project_files: Optional[dict[str, str]] = None) -> str:
        """
        Recursively documents the module tree from the leaves upwards.
        For each node, it first ensures its children are documented, then uses
        their documentation (not code) to inform its own documentation.

        Args:
            node: The current module/package node to document
            project_files: Project-level files for root documentation

        Returns:
            The generated documentation for the current node
        """
        if node.processed:
            return node.documentation

        # Step 1: Recursively document all children first (bottom-up approach)
        for child in node.children:
            self.document_module_tree_bottom_up(child, project_files)

        # Step 2: Now, document the current node
        logger.info(f"Documenting: {node.name} (Path: {node.path})")

        # Special handling for root project
        if node.is_root:
            node.documentation = self._document_project_root(node, project_files or {})
        else:
            node.documentation = self._document_node(node)

        # Save documentation to file
        success = file_manager.save_documentation(node, node.documentation)
        if success:
            node.processed = True
            logger.info(f"Successfully documented: {node.name}")
        else:
            logger.error(f"Failed to save documentation for: {node.name}")

        return node.documentation

    def _document_project_root(self, node: ModuleNode, project_files: dict[str, str]) -> str:
        """
        Generate documentation for the root project using project-level context files.

        Args:
            node: The root project node
            project_files: Dictionary containing project file contents

        Returns:
            Generated documentation for the project
        """
        logger.info(f"Documenting project root: {node.name}")

        # Collect children documentation
        children_docs = []
        for child in node.children:
            if child.documentation:
                children_docs.append(f"\n### {child.name}\n{child.documentation}")
            else:
                children_docs.append(f"\n### {child.name} (No documentation generated)\n")

        return llm_client.generate_project_documentation(project_files, children_docs)

    def _document_node(self, node: ModuleNode) -> str:
        """
        Generate documentation for a module or package node.

        Args:
            node: The ModuleNode to document

        Returns:
            Generated documentation for the node
        """
        if node.is_package:
            return self._document_package(node)
        return self._document_module(node)

    def _document_package(self, node: ModuleNode) -> str:
        """
        Generate documentation for a Python package.

        Args:
            node: The package ModuleNode to document

        Returns:
            Generated documentation for the package
        """
        # Collect children documentation
        children_docs = []
        for child in node.children:
            if child.documentation:
                children_docs.append(
                    f"\n--- Sub-module/Package: {child.name} Documentation ---\n"
                    f"{child.documentation}\n"
                    f"------------------------------------------------\n"
                )
            else:
                children_docs.append(
                    f"\n--- Sub-module/Package: {child.name} (No documentation generated) ---\n"
                )

        # Read __init__.py content if it exists
        init_content = file_manager.read_init_file(Path(node.path))

        return llm_client.generate_package_documentation(
            node.name, children_docs, init_content
        )

    def _document_module(self, node: ModuleNode) -> str:
        """
        Generate documentation for a Python module.

        Args:
            node: The module ModuleNode to document

        Returns:
            Generated documentation for the module
        """
        return llm_client.generate_module_documentation(node.name, node.content)

    def get_documentation_summary(self, node: ModuleNode, level: int = 0) -> str:
        """
        Generate a summary of all generated documentation.

        Args:
            node: Root node of the documentation tree
            level: Current indentation level

        Returns:
            Formatted documentation summary
        """
        indent = "  " * level
        node_type = "Project" if node.is_root else ("Package" if node.is_package else "Module")
        summary = f"{indent}- {node.name} ({node_type}):\n"

        if node.documentation:
            # Indent the documentation for better readability
            indented_doc = "\n".join(
                [indent + "  " + line for line in node.documentation.splitlines()]
            )
            summary += f"{indented_doc}\n"
        else:
            summary += f"{indent}  (No documentation generated for this node)\n"

        # Sort children by name for consistent output
        sorted_children = sorted(node.children, key=lambda c: c.name)
        for child in sorted_children:
            summary += self.get_documentation_summary(child, level + 1)

        return summary

    def validate_documentation(self, node: ModuleNode) -> dict[str, any]:
        """
        Validate the generated documentation for completeness and quality.

        Args:
            node: Root node of the documentation tree

        Returns:
            Dictionary containing validation results
        """
        issues = []
        warnings = []
        stats = {
            'total_nodes': 0,
            'documented_nodes': 0,
            'failed_nodes': 0,
            'empty_documentation': 0
        }

        def _validate_recursive(current_node: ModuleNode) -> None:
            stats['total_nodes'] += 1

            if not current_node.processed:
                stats['failed_nodes'] += 1
                issues.append(f"Node '{current_node.name}' was not processed")
            elif current_node.documentation:
                if current_node.documentation.startswith("Error:"):
                    stats['failed_nodes'] += 1
                    issues.append(f"Node '{current_node.name}' has error in documentation")
                elif len(current_node.documentation.strip()) < 50:
                    stats['empty_documentation'] += 1
                    warnings.append(f"Node '{current_node.name}' has very short documentation")
                else:
                    stats['documented_nodes'] += 1
            else:
                stats['empty_documentation'] += 1
                warnings.append(f"Node '{current_node.name}' has no documentation")

            for child in current_node.children:
                _validate_recursive(child)

        _validate_recursive(node)

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'stats': stats
        }


# Global documentation generator instance
doc_generator = DocumentationGenerator()
