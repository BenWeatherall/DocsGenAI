"""
Documentation generation logic for GenAI Docs.

This module handles the bottom-up documentation generation process,
orchestrating the documentation of modules, packages, and projects.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .cache import DocumentationCache
from .core_types import ModuleNode
from .dependency_analyzer import DependencyAnalyzer
from .dependency_graph_builder import DependencyGraphBuilder
from .exceptions import DocumentationError
from .file_manager import file_manager
from .llm_client import LLMClient
from .progress import ProgressTracker

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
_template_dir = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(_template_dir))


class DocumentationGenerator:
    """Handles the documentation generation process."""

    def __init__(self, llm_client: LLMClient) -> None:
        """
        Initialize the documentation generator.

        Args:
            llm_client: The LLM client instance to use for documentation generation
        """
        self.llm_client: LLMClient = llm_client
        self.use_dependency_graph: bool = True
        self.cache: DocumentationCache | None = None
        self.force_regenerate: bool = False
        self.progress_tracker: ProgressTracker | None = None

    def document_module_tree_bottom_up(
        self,
        node: ModuleNode,
        project_files: dict[str, str] | None = None,
        use_dependency_ordering: bool | None = None,
    ) -> str:
        """
        Recursively documents the module tree from the leaves upwards.
        For each node, it first ensures its children are documented, then uses
        their documentation (not code) to inform its own documentation.

        Args:
            node: The current module/package node to document
            project_files: Project-level files for root documentation
            use_dependency_ordering: If True, use dependency-aware ordering (default: self.use_dependency_graph)

        Returns:
            The generated documentation for the current node
        """
        if use_dependency_ordering is None:
            use_dependency_ordering = self.use_dependency_graph

        if use_dependency_ordering:
            return self._document_with_dependency_graph(node, project_files)
        return self._document_tree_recursive(node, project_files)

    def _document_with_dependency_graph(
        self, node: ModuleNode, project_files: dict[str, str] | None = None
    ) -> str:
        """
        Document modules using dependency-aware ordering.

        Args:
            node: Root node of the module tree
            project_files: Project-level files for root documentation

        Returns:
            Generated documentation for the root node
        """
        # Collect all nodes from the tree
        all_nodes = self._get_all_nodes(node)

        # Build dependency graph
        logger.info("Building dependency graph...")
        graph_builder = DependencyGraphBuilder(node.path)
        dependency_graph = graph_builder.build_graph(all_nodes)

        # Analyze graph for ordering
        analyzer = DependencyAnalyzer()
        cycles = analyzer._detect_cycles(dependency_graph)

        # Handle cycles by grouping them
        cycle_nodes = set()
        for cycle in cycles:
            cycle_nodes.update(cycle)

        # Get documentation order (topological if no cycles, otherwise dependency count)
        try:
            doc_order = analyzer.get_documentation_order(dependency_graph)
        except ValueError:
            # Fallback if cycles prevent topological sort
            logger.warning("Cycles detected, using dependency count ordering")
            doc_order = sorted(all_nodes, key=lambda x: len(x.dependencies))

        # Initialize progress tracker
        if self.progress_tracker is None:
            total_nodes = len(doc_order) + len(cycles)
            self.progress_tracker = ProgressTracker(total_nodes, enabled=True)

        # Document nodes in dependency order
        for module_node in doc_order:
            if module_node.processed:
                continue

            # Skip if this node is part of a cycle (will handle separately)
            if module_node in cycle_nodes:
                continue

            logger.info(f"Documenting: {module_node.name} (Path: {module_node.path})")

            # Update progress
            if self.progress_tracker:
                self.progress_tracker.update(module_node.name)

            # Check cache first
            file_path = module_node.get_file_path()
            cached_doc = None
            if self.cache and not self.force_regenerate:
                if self.cache.is_cached(module_node.path, file_path):
                    cached_doc = self.cache.get_cached_documentation(module_node.path)
                    logger.info(f"Using cached documentation for: {module_node.name}")

            if cached_doc:
                module_node.documentation = cached_doc
                module_node.processed = True
            else:
                # Get dependency context
                dep_context = self._get_dependency_context(module_node)

                try:
                    # Document the module
                    if module_node.is_package:
                        module_node.documentation = self._document_package(
                            module_node, dep_context
                        )
                    else:
                        module_node.documentation = self._document_module(
                            module_node, dep_context
                        )

                    # Cache the documentation
                    if self.cache:
                        self.cache.cache_documentation(
                            module_node.path, file_path, module_node.documentation
                        )

                    # Save documentation
                    success = file_manager.save_documentation(
                        module_node, module_node.documentation
                    )
                    if success:
                        module_node.processed = True
                        logger.info(f"Successfully documented: {module_node.name}")
                    else:
                        logger.error(
                            f"Failed to save documentation for: {module_node.name}"
                        )
                        raise DocumentationError(
                            f"Failed to save documentation for {module_node.name}"
                        )
                except Exception as e:
                    logger.error(f"Error documenting {module_node.name}: {e}")
                    module_node.documentation = (
                        f"Error: Failed to generate documentation: {e}"
                    )
                    module_node.processed = False
                    raise DocumentationError(
                        f"Failed to document {module_node.name}"
                    ) from e

        # Handle cycles - document all nodes in cycle together
        for cycle in cycles:
            logger.info(
                f"Documenting circular dependency group: {[n.name for n in cycle]}"
            )
            for cycle_node in cycle:
                # Update progress
                if self.progress_tracker:
                    self.progress_tracker.update(cycle_node.name)
                if cycle_node.processed:
                    continue

                # Check cache
                file_path = cycle_node.get_file_path()
                cached_doc = None
                if self.cache and not self.force_regenerate:
                    if self.cache.is_cached(cycle_node.path, file_path):
                        cached_doc = self.cache.get_cached_documentation(
                            cycle_node.path
                        )
                        logger.info(
                            f"Using cached documentation for: {cycle_node.name}"
                        )

                if cached_doc:
                    cycle_node.documentation = cached_doc
                    cycle_node.processed = True
                else:
                    # Get dependency context (excluding other cycle members to avoid circular references)
                    dep_context = self._get_dependency_context(
                        cycle_node, exclude_nodes=set(cycle)
                    )

                    try:
                        if cycle_node.is_package:
                            cycle_node.documentation = self._document_package(
                                cycle_node, dep_context
                            )
                        else:
                            cycle_node.documentation = self._document_module(
                                cycle_node, dep_context
                            )

                        # Cache the documentation
                        if self.cache:
                            self.cache.cache_documentation(
                                cycle_node.path, file_path, cycle_node.documentation
                            )

                        success = file_manager.save_documentation(
                            cycle_node, cycle_node.documentation
                        )
                        if success:
                            cycle_node.processed = True
                        else:
                            raise DocumentationError(
                                f"Failed to save documentation for {cycle_node.name}"
                            )
                    except Exception as e:
                        logger.error(f"Error documenting {cycle_node.name}: {e}")
                        cycle_node.documentation = (
                            f"Error: Failed to generate documentation: {e}"
                        )
                        cycle_node.processed = False

        # Finally, document root if it hasn't been done
        if node.is_root and not node.processed:
            if self.progress_tracker:
                self.progress_tracker.update(node.name)
            node.documentation = self._document_project_root(node, project_files or {})
            success = file_manager.save_documentation(node, node.documentation)
            if success:
                node.processed = True

        # Finish progress tracking
        if self.progress_tracker:
            self.progress_tracker.finish()

        return node.documentation or ""

    def _document_tree_recursive(
        self, node: ModuleNode, project_files: dict[str, str] | None = None
    ) -> str:
        """
        Recursively documents the module tree from the leaves upwards (original method).

        Args:
            node: The current module/package node to document
            project_files: Project-level files for root documentation

        Returns:
            The generated documentation for the current node
        """
        if node.processed:
            return node.documentation or ""

        # Step 1: Recursively document all children first (bottom-up approach)
        for child in node.children:
            self._document_tree_recursive(child, project_files)

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
            raise DocumentationError(f"Failed to save documentation for {node.name}")

        return node.documentation or ""

    def _get_all_nodes(self, root_node: ModuleNode) -> list[ModuleNode]:
        """
        Get all nodes from the tree recursively.

        Args:
            root_node: Root node of the tree

        Returns:
            List of all ModuleNode objects
        """
        nodes = [root_node]
        for child in root_node.children:
            nodes.extend(self._get_all_nodes(child))
        return nodes

    def _get_dependency_context(
        self, node: ModuleNode, exclude_nodes: set[ModuleNode] | None = None
    ) -> dict[str, str]:
        """
        Get documentation context from dependencies.

        Args:
            node: ModuleNode to get dependencies for
            exclude_nodes: Set of nodes to exclude from context

        Returns:
            Dictionary mapping dependency names to their documentation summaries
        """
        if exclude_nodes is None:
            exclude_nodes = set()

        context = {}
        for dep in node.dependencies:
            if dep in exclude_nodes:
                continue
            if dep.documentation and dep.processed:
                # Extract a summary from the documentation
                summary = (
                    dep.documentation[:200] + "..."
                    if len(dep.documentation) > 200
                    else dep.documentation
                )
                context[dep.name] = summary
        return context

    def _document_project_root(
        self, node: ModuleNode, project_files: dict[str, str]
    ) -> str:
        """
        Generate documentation for the root project using project-level context files.

        Args:
            node: The root project node
            project_files: Dictionary containing project file contents

        Returns:
            Generated documentation for the project
        """
        logger.info(f"Documenting project root: {node.name}")

        # Collect children documentation using Jinja template
        template = _jinja_env.get_template("project_child_documentation.j2")
        children_docs = []
        for child in node.children:
            children_docs.append(template.render(child=child))

        return self.llm_client.generate_project_documentation(
            project_files, children_docs
        )

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

    def _document_package(
        self, node: ModuleNode, dependency_context: dict[str, str] | None = None
    ) -> str:
        """
        Generate documentation for a Python package.

        Args:
            node: The package ModuleNode to document
            dependency_context: Optional context from dependencies

        Returns:
            Generated documentation for the package
        """
        # Collect children documentation using Jinja template
        template = _jinja_env.get_template("child_documentation.j2")
        children_docs = []
        for child in node.children:
            children_docs.append(template.render(child=child))

        # Read __init__.py content if it exists
        init_content = file_manager.read_init_file(Path(node.path))

        # Format dependency context using Jinja template
        dep_context_str = ""
        if dependency_context:
            dep_template = _jinja_env.get_template("dependency_context.j2")
            dep_context_str = dep_template.render(dependencies=dependency_context)

        return self.llm_client.generate_package_documentation(
            node.name, children_docs, init_content, dependency_context=dep_context_str
        )

    def _document_module(
        self, node: ModuleNode, dependency_context: dict[str, str] | None = None
    ) -> str:
        """
        Generate documentation for a Python module.

        Args:
            node: The module ModuleNode to document
            dependency_context: Optional context from dependencies

        Returns:
            Generated documentation for the module
        """
        # Format dependency context using Jinja template
        dep_context_str = ""
        if dependency_context:
            dep_template = _jinja_env.get_template("dependency_context.j2")
            dep_context_str = dep_template.render(dependencies=dependency_context)

        return self.llm_client.generate_module_documentation(
            node.name, node.content, dependency_context=dep_context_str
        )

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
        node_type = (
            "Project" if node.is_root else ("Package" if node.is_package else "Module")
        )
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

    def validate_documentation(self, node: ModuleNode) -> dict[str, Any]:
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
            "total_nodes": 0,
            "documented_nodes": 0,
            "failed_nodes": 0,
            "empty_documentation": 0,
        }

        def _validate_recursive(current_node: ModuleNode) -> None:
            stats["total_nodes"] += 1

            if not current_node.processed:
                stats["failed_nodes"] += 1
                issues.append(f"Node '{current_node.name}' was not processed")
            elif current_node.documentation:
                if current_node.documentation.startswith("Error:"):
                    stats["failed_nodes"] += 1
                    issues.append(
                        f"Node '{current_node.name}' has error in documentation"
                    )
                elif len(current_node.documentation.strip()) < 50:
                    stats["empty_documentation"] += 1
                    warnings.append(
                        f"Node '{current_node.name}' has very short documentation"
                    )
                else:
                    stats["documented_nodes"] += 1
            else:
                stats["empty_documentation"] += 1
                warnings.append(f"Node '{current_node.name}' has no documentation")

            for child in current_node.children:
                _validate_recursive(child)

        _validate_recursive(node)

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "stats": stats,
        }
