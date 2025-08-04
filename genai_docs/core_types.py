"""
Core data types for the GenAI Docs dependency graph system.

This module provides the foundational data structures used throughout the
dependency analysis and documentation generation system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ImportStatement:
    """
    Represents a single import statement extracted from Python code.

    Attributes:
        module_name: The name of the module being imported
        alias: Optional alias for the import (e.g., 'import os as operating_system')
        from_import: True if this is a 'from x import y' statement
        imported_items: list of specific items imported (for from-imports)
        line_number: Line number where this import appears
        is_relative: True if this is a relative import (e.g., 'from . import x')
        relative_level: Number of dots in relative import (e.g., 2 for 'from .. import x')
    """
    module_name: str
    alias: Optional[str] = None
    from_import: bool = False
    imported_items: list[str] = field(default_factory=list)
    line_number: int = 0
    is_relative: bool = False
    relative_level: int = 0

    def __repr__(self) -> str:
        if self.from_import:
            items = ", ".join(self.imported_items) if self.imported_items else "*"
            return f"from {self.module_name} import {items}"
        alias_part = f" as {self.alias}" if self.alias else ""
        return f"import {self.module_name}{alias_part}"


@dataclass
class ModuleNode:
    """
    Enhanced ModuleNode representing a Python module or package with dependency tracking.

    This is the core data structure that represents modules/packages in the
    dependency graph system. It extends the basic ModuleNode with dependency
    analysis capabilities and documentation state management.

    Attributes:
        path: Full file system path to the module/package
        name: Name of the module or package
        is_package: True if it's a package (directory with __init__.py)
        is_root: True if this is the root project node
        children: list of child ModuleNode objects
        content: Raw code content for .py files or __init__.py for packages
        documentation: Generated documentation from the LLM
        processed: Flag to track if this node has been documented

        # Dependency tracking fields
        dependencies: list of ModuleNode objects this module depends on
        dependents: list of ModuleNode objects that depend on this module
        import_statements: list of ImportStatement objects extracted from code
        resolved_imports: Mapping of import names to resolved file paths

        # Documentation state management
        documentation_state: Current state of documentation ("pending", "in_progress", "completed", "failed")
        dependency_context: Documentation context from dependencies

        # Cycle handling
        cycle_group: list of ModuleNode objects in the same circular dependency group
        is_cycle_representative: True if this node represents its cycle group
    """
    # Basic module information
    path: str
    name: str
    is_package: bool = False
    is_root: bool = False
    children: list['ModuleNode'] = field(default_factory=list)
    content: Optional[str] = None
    documentation: Optional[str] = None
    processed: bool = False

    # Dependency tracking
    dependencies: list['ModuleNode'] = field(default_factory=list)
    dependents: list['ModuleNode'] = field(default_factory=list)
    import_statements: list[ImportStatement] = field(default_factory=list)
    resolved_imports: dict[str, str] = field(default_factory=dict)

    # Documentation state management
    documentation_state: str = "pending"  # pending, in_progress, completed, failed
    dependency_context: dict[str, str] = field(default_factory=dict)

    # Cycle handling
    cycle_group: Optional[list['ModuleNode']] = None
    is_cycle_representative: bool = False

    def add_child(self, child_node: 'ModuleNode') -> None:
        """Adds a child module/package to this node."""
        self.children.append(child_node)

    def add_dependency(self, dependency_node: 'ModuleNode') -> None:
        """Adds a dependency relationship to this node."""
        if dependency_node not in self.dependencies:
            self.dependencies.append(dependency_node)
        if self not in dependency_node.dependents:
            dependency_node.dependents.append(self)

    def remove_dependency(self, dependency_node: 'ModuleNode') -> None:
        """Removes a dependency relationship from this node."""
        if dependency_node in self.dependencies:
            self.dependencies.remove(dependency_node)
        if self in dependency_node.dependents:
            dependency_node.dependents.remove(self)

    def get_all_dependencies(self) -> set['ModuleNode']:
        """Returns all dependencies (direct and indirect) of this node."""
        all_deps = set()
        for dep in self.dependencies:
            all_deps.add(dep)
            all_deps.update(dep.get_all_dependencies())
        return all_deps

    def get_all_dependents(self) -> set['ModuleNode']:
        """Returns all dependents (direct and indirect) of this node."""
        all_deps = set()
        for dep in self.dependents:
            all_deps.add(dep)
            all_deps.update(dep.get_all_dependents())
        return all_deps

    def is_leaf(self) -> bool:
        """Returns True if this node has no children."""
        return len(self.children) == 0

    def is_leaf_module(self) -> bool:
        """Returns True if this is a leaf module (no children and not a package)."""
        return self.is_leaf() and not self.is_package

    def get_file_path(self) -> Path:
        """Returns the Path object for this module's file."""
        if self.is_package:
            return Path(self.path) / "__init__.py"
        return Path(self.path)

    def get_module_name(self) -> str:
        """Returns the full module name (e.g., 'package.submodule')."""
        if self.is_root:
            return self.name
        # This will be enhanced when we build the full module tree
        return self.name

    def __hash__(self) -> int:
        """Make ModuleNode hashable for use in sets."""
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on path."""
        if not isinstance(other, ModuleNode):
            return False
        return self.path == other.path

    def __repr__(self) -> str:
        """String representation for debugging."""
        deps_count = len(self.dependencies)
        state = f"({self.documentation_state})" if self.documentation_state != "pending" else ""
        return f"ModuleNode(name='{self.name}', is_package={self.is_package}, deps={deps_count}{state})"


@dataclass
class DependencyGraph:
    """
    Represents the complete dependency graph of a Python project.

    This class manages the overall dependency relationships between all
    modules in a project, providing methods for analysis and traversal.

    Attributes:
        nodes: Dictionary mapping module paths to ModuleNode objects
        root_node: The root project ModuleNode
        cycles: list of detected circular dependency groups
        topological_order: list of nodes in topological order (if computed)
    """
    nodes: dict[str, ModuleNode] = field(default_factory=dict)
    root_node: Optional[ModuleNode] = None
    cycles: list[list[ModuleNode]] = field(default_factory=list)
    topological_order: list[ModuleNode] = field(default_factory=list)

    def add_node(self, node: ModuleNode) -> None:
        """Adds a node to the graph."""
        self.nodes[node.path] = node
        if node.is_root:
            self.root_node = node

    def get_node(self, path: str) -> Optional[ModuleNode]:
        """Returns a node by its path."""
        return self.nodes.get(path)

    def get_node_by_name(self, name: str) -> Optional[ModuleNode]:
        """Returns a node by its name."""
        for node in self.nodes.values():
            if node.name == name:
                return node
        return None

    def get_all_nodes(self) -> list[ModuleNode]:
        """Returns all nodes in the graph."""
        return list(self.nodes.values())

    def get_leaf_nodes(self) -> list[ModuleNode]:
        """Returns all leaf nodes (nodes with no dependencies)."""
        return [node for node in self.nodes.values() if len(node.dependencies) == 0]

    def get_root_nodes(self) -> list[ModuleNode]:
        """Returns all root nodes (nodes with no dependents)."""
        return [node for node in self.nodes.values() if len(node.dependents) == 0]

    def has_cycles(self) -> bool:
        """Returns True if the graph contains circular dependencies."""
        return len(self.cycles) > 0

    def get_cycle_count(self) -> int:
        """Returns the number of circular dependency groups."""
        return len(self.cycles)

    def get_node_count(self) -> int:
        """Returns the total number of nodes in the graph."""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """Returns the total number of dependency relationships."""
        total_edges = 0
        for node in self.nodes.values():
            total_edges += len(node.dependencies)
        return total_edges

    def clear_analysis(self) -> None:
        """Clears all analysis results (cycles, topological order, etc.)."""
        self.cycles.clear()
        self.topological_order.clear()
        for node in self.nodes.values():
            node.cycle_group = None
            node.is_cycle_representative = False

    def __repr__(self) -> str:
        """String representation for debugging."""
        node_count = self.get_node_count()
        edge_count = self.get_edge_count()
        cycle_count = self.get_cycle_count()
        return f"DependencyGraph(nodes={node_count}, edges={edge_count}, cycles={cycle_count})"


@dataclass
class DocumentationContext:
    """
    Represents the context passed between modules during documentation generation.

    This class manages the context information that flows from dependencies
    to dependents during the documentation process.

    Attributes:
        module_summaries: Dictionary mapping module names to their documentation summaries
        interface_descriptions: Dictionary mapping module names to their public interfaces
        usage_examples: Dictionary mapping module names to usage examples
        relationships: Dictionary mapping module names to their relationship descriptions
    """
    module_summaries: dict[str, str] = field(default_factory=dict)
    interface_descriptions: dict[str, str] = field(default_factory=dict)
    usage_examples: dict[str, str] = field(default_factory=dict)
    relationships: dict[str, str] = field(default_factory=dict)

    def add_module_context(self, module_name: str, summary: str, interface: str = "",
                          examples: str = "", relationships: str = "") -> None:
        """Adds context information for a specific module."""
        self.module_summaries[module_name] = summary
        if interface:
            self.interface_descriptions[module_name] = interface
        if examples:
            self.usage_examples[module_name] = examples
        if relationships:
            self.relationships[module_name] = relationships

    def get_module_context(self, module_name: str) -> dict[str, str]:
        """Returns all context information for a specific module."""
        return {
            'summary': self.module_summaries.get(module_name, ''),
            'interface': self.interface_descriptions.get(module_name, ''),
            'examples': self.usage_examples.get(module_name, ''),
            'relationships': self.relationships.get(module_name, '')
        }

    def get_dependency_context_string(self, dependencies: list[ModuleNode]) -> str:
        """Returns a formatted string of dependency context for documentation."""
        if not dependencies:
            return ""

        context_parts = []
        for dep in dependencies:
            dep_name = dep.get_module_name()
            dep_context = self.get_module_context(dep_name)

            if dep_context['summary']:
                context_parts.append(f"**{dep_name}**: {dep_context['summary']}")

            if dep_context['interface']:
                context_parts.append(f"**{dep_name} Interface**: {dep_context['interface']}")

        if context_parts:
            return "\n\n**Dependencies:**\n" + "\n".join(context_parts)
        return ""

    def __repr__(self) -> str:
        """String representation for debugging."""
        module_count = len(self.module_summaries)
        return f"DocumentationContext(modules={module_count})"
