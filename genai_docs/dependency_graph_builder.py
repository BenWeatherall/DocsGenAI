"""
Dependency graph builder module.

This module provides functionality to build dependency graphs
from Python project modules and their import statements.
"""

from pathlib import Path
from typing import Optional

from .ast_analyzer import ASTAnalyzer
from .core_types import DependencyGraph, ImportStatement, ModuleNode


class DependencyGraphBuilder:
    """
    Builds dependency graphs from Python project modules.

    This class takes ModuleNode objects and their import statements to construct
    a complete dependency graph that can be analyzed for ordering and cycles.
    """

    def __init__(self, project_root: str):
        """
        Initialize the dependency graph builder.

        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root).resolve()
        self.ast_analyzer = ASTAnalyzer(str(project_root))
        self.module_path_map: dict[str, ModuleNode] = {}

    def build_graph(self, module_nodes: list[ModuleNode]) -> DependencyGraph:
        """
        Build a dependency graph from a list of module nodes.

        Args:
            module_nodes: list of ModuleNode objects to analyze

        Returns:
            DependencyGraph object representing the project dependencies
        """
        # Create the graph
        graph = DependencyGraph()

        # Add all nodes to the graph
        for node in module_nodes:
            graph.add_node(node)
            self.module_path_map[node.path] = node

        # Analyze imports for all modules
        project_imports = self.ast_analyzer.analyze_project_imports(module_nodes)

        # Store import statements in nodes
        for node in module_nodes:
            if node.path in project_imports:
                node.import_statements = project_imports[node.path]

        # Build dependency relationships
        self._build_dependencies(graph, project_imports)

        return graph

    def _build_dependencies(self, graph: DependencyGraph,
                          project_imports: dict[str, list[ImportStatement]]) -> None:
        """
        Build dependency relationships between modules.

        Args:
            graph: The DependencyGraph to populate
            project_imports: Dictionary mapping module paths to import statements
        """
        for module_path, import_statements in project_imports.items():
            source_node = graph.get_node(module_path)
            if not source_node:
                continue

            for import_stmt in import_statements:
                # Skip external imports
                if self.ast_analyzer.is_external_import(import_stmt):
                    continue

                # Resolve the import to a target module
                target_node = self._resolve_import_to_module(import_stmt, source_node)
                if target_node and target_node != source_node:
                    source_node.add_dependency(target_node)

    def _resolve_import_to_module(self, import_stmt: ImportStatement,
                                source_node: ModuleNode) -> Optional[ModuleNode]:
        """
        Resolve an import statement to a ModuleNode.

        Args:
            import_stmt: The ImportStatement to resolve
            source_node: The ModuleNode containing the import

        Returns:
            ModuleNode if found, None otherwise
        """
        if import_stmt.is_relative:
            return self._resolve_relative_import(import_stmt, source_node)
        return self._resolve_absolute_import(import_stmt, source_node)

    def _resolve_relative_import(self, import_stmt: ImportStatement,
                               source_node: ModuleNode) -> Optional[ModuleNode]:
        """
        Resolve a relative import to a ModuleNode.

        Args:
            import_stmt: The ImportStatement to resolve
            source_node: The ModuleNode containing the import

        Returns:
            ModuleNode if found, None otherwise
        """
        # Calculate the target path based on relative import
        source_path = Path(source_node.path)

        if import_stmt.module_name.startswith('.'):
            # Relative import
            dots = len(import_stmt.module_name) - len(import_stmt.module_name.lstrip('.'))
            target_module = import_stmt.module_name[dots:]

            if dots == 1:
                # Same level import
                target_path = source_path.parent / f"{target_module}.py"
            else:
                # Parent level import
                parent_levels = dots - 1
                target_path = source_path.parent
                for _ in range(parent_levels):
                    target_path = target_path.parent
                target_path = target_path / f"{target_module}.py"
        else:
            # Absolute import within project
            target_path = self.project_root / f"{import_stmt.module_name}.py"

        # Check if target exists in our module map
        return self.module_path_map.get(str(target_path))

    def _resolve_absolute_import(self, import_stmt: ImportStatement,
                               source_node: ModuleNode) -> Optional[ModuleNode]:
        """
        Resolve an absolute import to a ModuleNode.

        Args:
            import_stmt: The ImportStatement to resolve
            source_node: The ModuleNode containing the import

        Returns:
            ModuleNode if found, None otherwise
        """
        # For absolute imports, we need to check if the module is within our project
        target_path = self.project_root / f"{import_stmt.module_name}.py"

        # Check if target exists in our module map
        return self.module_path_map.get(str(target_path))
