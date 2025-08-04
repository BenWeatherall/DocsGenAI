"""
Core dependency graph module.

This module provides the main DependencyGraph class and re-exports
the builder and analyzer components for convenience.
"""

from typing import Any, Dict, List, Optional, Tuple

import networkx as nx


class DependencyGraph:
    """
    A graph representation of module dependencies.

    This class provides a simple graph interface for tracking dependencies
    between modules using node names and data dictionaries.
    """

    def __init__(self):
        """Initialize an empty dependency graph."""
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def add_node(self, name: str, data: Dict[str, Any]) -> None:
        """
        Add a node to the graph.

        Args:
            name: Node identifier
            data: Node data dictionary
        """
        self.nodes[name] = data.copy()

    def add_edge(self, from_node: str, to_node: str, edge_type: str = "imports") -> None:
        """
        Add an edge between two nodes.

        Args:
            from_node: Source node name
            to_node: Target node name
            edge_type: Type of dependency relationship
        """
        if from_node not in self.nodes:
            self.nodes[from_node] = {}
        if to_node not in self.nodes:
            self.nodes[to_node] = {}

        self.edges[from_node, to_node] = {"type": edge_type}

    def remove_node(self, name: str) -> None:
        """
        Remove a node and all its edges from the graph.

        Args:
            name: Node name to remove
        """
        if name in self.nodes:
            del self.nodes[name]

        # Remove all edges involving this node
        edges_to_remove = []
        for edge in self.edges:
            if name in edge:
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self.edges[edge]

    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get node data by name.

        Args:
            name: Node name

        Returns:
            Node data dictionary or None if not found
        """
        return self.nodes.get(name)

    def get_neighbors(self, name: str) -> List[str]:
        """
        Get all neighbors of a node.

        Args:
            name: Node name

        Returns:
            List of neighbor node names
        """
        neighbors = []
        for (from_node, to_node) in self.edges:
            if from_node == name:
                neighbors.append(to_node)
            elif to_node == name:
                neighbors.append(from_node)
        return neighbors

    def has_cycle(self) -> bool:
        """
        Check if the graph contains cycles.

        Returns:
            True if cycles exist, False otherwise
        """
        try:
            # Convert to NetworkX graph for cycle detection
            nx_graph = nx.DiGraph()

            # Add nodes
            for node_name in self.nodes:
                nx_graph.add_node(node_name)

            # Add edges
            for (from_node, to_node) in self.edges:
                nx_graph.add_edge(from_node, to_node)

            # Check for cycles
            return len(list(nx.simple_cycles(nx_graph))) > 0
        except nx.NetworkXNoCycle:
            return False

    def topological_sort(self) -> List[str]:
        """
        Perform topological sorting of the graph.

        Returns:
            List of node names in topological order

        Raises:
            ValueError: If graph contains cycles
        """
        try:
            # Convert to NetworkX graph for topological sort
            nx_graph = nx.DiGraph()

            # Add nodes
            for node_name in self.nodes:
                nx_graph.add_node(node_name)

            # Add edges
            for (from_node, to_node) in self.edges:
                nx_graph.add_edge(from_node, to_node)

            # Generate topological order
            return list(nx.topological_sort(nx_graph))
        except (nx.NetworkXError, nx.NetworkXUnfeasible) as e:
            if "cycle" in str(e).lower():
                raise ValueError("Graph contains cycles") from e
            raise

    def find_cycles(self) -> List[List[str]]:
        """
        Find all cycles in the graph.

        Returns:
            List of cycles, where each cycle is a list of node names
        """
        try:
            # Convert to NetworkX graph for cycle detection
            nx_graph = nx.DiGraph()

            # Add nodes
            for node_name in self.nodes:
                nx_graph.add_node(node_name)

            # Add edges
            for (from_node, to_node) in self.edges:
                nx_graph.add_edge(from_node, to_node)

            # Find cycles
            return list(nx.simple_cycles(nx_graph))
        except nx.NetworkXNoCycle:
            return []

    def get_dependency_path(self, from_node: str, to_node: str) -> Optional[List[str]]:
        """
        Get the dependency path between two nodes.

        Args:
            from_node: Source node name
            to_node: Target node name

        Returns:
            List of node names in the path, or None if no path exists
        """
        try:
            # Convert to NetworkX graph for path finding
            nx_graph = nx.DiGraph()

            # Add nodes
            for node_name in self.nodes:
                nx_graph.add_node(node_name)

            # Add edges
            for (from_n, to_n) in self.edges:
                nx_graph.add_edge(from_n, to_n)

            # Find path
            path = nx.shortest_path(nx_graph, from_node, to_node)
            return path
        except nx.NetworkXNoPath:
            return None

    def get_reverse_dependencies(self, node_name: str) -> List[str]:
        """
        Get all nodes that depend on the given node.

        Args:
            node_name: Node name

        Returns:
            List of node names that depend on the given node
        """
        dependents = []
        for (from_node, to_node) in self.edges:
            if to_node == node_name:
                dependents.append(from_node)
        return dependents

    def get_dependency_tree(self, node_name: str) -> Dict[str, Any]:
        """
        Get the dependency tree for a node.

        Args:
            node_name: Root node name

        Returns:
            Dictionary representing the dependency tree
        """
        tree = {node_name: {}}

        # Get direct dependencies
        for (from_node, to_node) in self.edges:
            if from_node == node_name:
                if to_node not in tree[node_name]:
                    tree[node_name][to_node] = {}
                # Recursively get dependencies of dependencies
                if to_node in self.nodes:
                    subtree = self.get_dependency_tree(to_node)
                    if to_node in subtree:
                        tree[node_name][to_node] = subtree[to_node]

        return tree

    def analyze_dependency_metrics(self) -> Dict[str, Any]:
        """
        Analyze dependency metrics for the graph.

        Returns:
            Dictionary containing various metrics
        """
        if not self.nodes:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "average_dependencies": 0,
                "max_dependencies": 0,
                "min_dependencies": 0,
                "cycles": 0
            }

        # Calculate basic metrics
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)

        # Calculate dependency counts per node
        dependency_counts = {}
        for node_name in self.nodes:
            count = 0
            for (from_node, to_node) in self.edges:
                if from_node == node_name:
                    count += 1
            dependency_counts[node_name] = count

        # Calculate statistics
        counts = list(dependency_counts.values())
        avg_deps = sum(counts) / len(counts) if counts else 0
        max_deps = max(counts) if counts else 0
        min_deps = min(counts) if counts else 0

        # Count cycles
        cycles = len(self.find_cycles())

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "average_dependencies": avg_deps,
            "max_dependencies": max_deps,
            "min_dependencies": min_deps,
            "cycles": cycles
        }

    def export_to_dot(self) -> str:
        """
        Export the graph to DOT format.

        Returns:
            DOT format string representation
        """
        dot_lines = ["digraph DependencyGraph {"]

        # Add nodes
        for node_name, node_data in self.nodes.items():
            label = node_data.get("name", node_name)
            dot_lines.append(f'    "{node_name}" [label="{label}"];')

        # Add edges
        for (from_node, to_node), edge_data in self.edges.items():
            edge_type = edge_data.get("type", "imports")
            dot_lines.append(f'    {from_node} -> {to_node} [label="{edge_type}"];')

        dot_lines.append("}")
        return "\n".join(dot_lines)

    def export_to_json(self) -> Dict[str, Any]:
        """
        Export the graph to JSON format.

        Returns:
            Dictionary representation of the graph
        """
        edges_list = []
        for (from_node, to_node), edge_data in self.edges.items():
            edges_list.append({
                "from": from_node,
                "to": to_node,
                "type": edge_data.get("type", "imports")
            })

        return {
            "nodes": self.nodes,
            "edges": edges_list
        }

    def clear_graph(self) -> None:
        """Clear all nodes and edges from the graph."""
        self.nodes.clear()
        self.edges.clear()

    def clear(self) -> None:
        """Clear all nodes and edges from the graph (alias for clear_graph)."""
        self.clear_graph()

    def get_subgraph(self, node_names: List[str]) -> 'DependencyGraph':
        """
        Get a subgraph containing only the specified nodes.

        Args:
            node_names: List of node names to include

        Returns:
            New DependencyGraph containing only the specified nodes
        """
        subgraph = DependencyGraph()

        # Add nodes
        for node_name in node_names:
            if node_name in self.nodes:
                subgraph.nodes[node_name] = self.nodes[node_name].copy()

        # Add edges
        for (from_node, to_node), edge_data in self.edges.items():
            if from_node in node_names and to_node in node_names:
                subgraph.edges[from_node, to_node] = edge_data.copy()

        return subgraph


# Re-export the builder and analyzer components
from .core_types import DependencyGraph as ModuleDependencyGraph
from .dependency_analyzer import DependencyAnalyzer
from .dependency_graph_builder import DependencyGraphBuilder

__all__ = ['DependencyAnalyzer', 'DependencyGraph', 'DependencyGraphBuilder', 'ModuleDependencyGraph']
