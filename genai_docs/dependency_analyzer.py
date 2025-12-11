"""
Dependency analyzer module.

This module provides functionality to analyze dependency graphs
for cycles, topological ordering, and metrics calculation.
"""

from typing import Any

import networkx as nx

from .core_types import DependencyGraph, ModuleNode


class DependencyAnalyzer:
    """
    Analyzes dependency graphs for various properties and metrics.

    This class provides methods to detect cycles, generate topological orders,
    calculate metrics, and validate dependency graphs.
    """

    def __init__(self):
        """Initialize the dependency analyzer."""

    def analyze_graph(self, graph: DependencyGraph) -> dict[str, Any]:
        """
        Perform comprehensive analysis of a dependency graph.

        Args:
            graph: The DependencyGraph to analyze

        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            "cycles": self._detect_cycles(graph),
            "topological_order": self._generate_topological_order(graph),
            "metrics": self._calculate_metrics(graph),
            "validation": self.validate_graph(graph),
        }

        return analysis

    def _detect_cycles(self, graph: DependencyGraph) -> list[list[ModuleNode]]:
        """
        Detect cycles in the dependency graph.

        Args:
            graph: The DependencyGraph to analyze

        Returns:
            List of cycles, where each cycle is a list of ModuleNode objects
        """
        cycles = []

        # Convert to NetworkX graph for cycle detection
        nx_graph = nx.DiGraph()

        # Add nodes
        for node in graph.get_all_nodes():
            nx_graph.add_node(node.name)

        # Add edges
        for node in graph.get_all_nodes():
            for dep in node.dependencies:
                nx_graph.add_edge(node.name, dep.name)

        # Find cycles
        try:
            cycle_nodes = list(nx.simple_cycles(nx_graph))
            for cycle in cycle_nodes:
                cycle_modules = []
                for node_name in cycle:
                    node = graph.get_node_by_name(node_name)
                    if node:
                        cycle_modules.append(node)
                if cycle_modules:
                    cycles.append(cycle_modules)
        except nx.NetworkXNoCycle:
            # No cycles found
            pass

        return cycles

    def _generate_topological_order(self, graph: DependencyGraph) -> list[ModuleNode]:
        """
        Generate topological ordering of modules.

        Uses NetworkX's topological sort algorithm to order modules such that
        dependencies come before dependents. This ensures documentation is
        generated in the correct order.

        Args:
            graph: The DependencyGraph to analyze

        Returns:
            List of ModuleNode objects in topological order

        Raises:
            ValueError: If the graph contains cycles (preventing topological sort)
        """
        # Convert to NetworkX graph for topological sort
        nx_graph = nx.DiGraph()

        # Add nodes (using node names as identifiers)
        for node in graph.get_all_nodes():
            nx_graph.add_node(node.name)

        # Add edges (dependencies: source depends on target)
        for node in graph.get_all_nodes():
            for dep in node.dependencies:
                nx_graph.add_edge(node.name, dep.name)

        try:
            # Generate topological order using NetworkX
            # This will fail if cycles exist
            sorted_names = list(nx.topological_sort(nx_graph))

            # Convert back to ModuleNode objects
            sorted_nodes = []
            for name in sorted_names:
                node = graph.get_node_by_name(name)
                if node:
                    sorted_nodes.append(node)

            return sorted_nodes
        except nx.NetworkXError as e:
            if "cycle" in str(e).lower():
                raise ValueError("Graph contains cycles") from e
            raise

    def _calculate_metrics(self, graph: DependencyGraph) -> dict[str, Any]:
        """
        Calculate various metrics for the dependency graph.

        Args:
            graph: The DependencyGraph to analyze

        Returns:
            Dictionary containing calculated metrics
        """
        nodes = graph.get_all_nodes()

        if not nodes:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "average_dependencies": 0,
                "max_dependencies": 0,
                "min_dependencies": 0,
                "dependency_distribution": {},
            }

        # Calculate basic metrics
        total_nodes = len(nodes)
        total_edges = sum(len(node.dependencies) for node in nodes)
        dependency_counts = [len(node.dependencies) for node in nodes]

        metrics = {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "average_dependencies": total_edges / total_nodes if total_nodes > 0 else 0,
            "max_dependencies": max(dependency_counts) if dependency_counts else 0,
            "min_dependencies": min(dependency_counts) if dependency_counts else 0,
            "dependency_distribution": {},
        }

        # Calculate dependency distribution
        for count in dependency_counts:
            metrics["dependency_distribution"][count] = (
                metrics["dependency_distribution"].get(count, 0) + 1
            )

        return metrics

    def get_documentation_order(self, graph: DependencyGraph) -> list[ModuleNode]:
        """
        Get the optimal order for documenting modules.

        Args:
            graph: The DependencyGraph to analyze

        Returns:
            List of ModuleNode objects in documentation order
        """
        try:
            return self._generate_topological_order(graph)
        except ValueError:
            # If there are cycles, return nodes in dependency count order
            nodes = graph.get_all_nodes()
            return sorted(nodes, key=lambda x: len(x.dependencies))

    def get_cycle_representatives(self, graph: DependencyGraph) -> list[ModuleNode]:
        """
        Get representative nodes from each cycle for documentation.

        Args:
            graph: The DependencyGraph to analyze

        Returns:
            List of ModuleNode objects representing cycles
        """
        cycles = self._detect_cycles(graph)
        representatives = []

        for cycle in cycles:
            if cycle:
                # Choose the node with the most dependencies as representative
                representative = max(cycle, key=lambda x: len(x.dependencies))
                representatives.append(representative)

        return representatives

    def validate_graph(self, graph: DependencyGraph) -> dict[str, Any]:
        """
        Validate the dependency graph and return validation results.

        Args:
            graph: The DependencyGraph to validate

        Returns:
            Dictionary containing validation results
        """
        validation = {"valid": True, "issues": [], "warnings": []}

        nodes = graph.get_all_nodes()

        # Check for cycles
        cycles = self._detect_cycles(graph)
        if cycles:
            validation["valid"] = False
            validation["issues"].append(
                f"Found {len(cycles)} circular dependency cycles"
            )

        # Check for orphaned nodes
        orphaned_nodes = [
            node
            for node in nodes
            if not node.dependencies
            and not any(node in dep.dependencies for dep in nodes)
        ]
        if orphaned_nodes:
            validation["warnings"].append(
                f"Found {len(orphaned_nodes)} orphaned modules"
            )

        # Check for high dependency counts
        high_dependency_nodes = [node for node in nodes if len(node.dependencies) > 10]
        if high_dependency_nodes:
            validation["warnings"].append(
                f"Found {len(high_dependency_nodes)} modules with high dependency counts (>10)"
            )

        return validation
