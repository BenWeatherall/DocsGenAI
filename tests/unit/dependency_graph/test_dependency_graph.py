"""
Unit tests for the dependency graph module.

This module tests the dependency graph functionality including
graph building, analysis, and visualization.
"""


import pytest

from genai_docs.dependency_graph import DependencyGraph


class TestDependencyGraph:
    """Test the DependencyGraph class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.graph = DependencyGraph()

    def test_add_node(self):
        """Test adding a node to the graph."""
        self.graph.add_node("module1", {"type": "module", "path": "/path/to/module1"})

        assert "module1" in self.graph.nodes
        assert self.graph.nodes["module1"]["type"] == "module"
        assert self.graph.nodes["module1"]["path"] == "/path/to/module1"

    def test_add_edge(self):
        """Test adding an edge between nodes."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_edge("module1", "module2", "imports")

        assert ("module1", "module2") in self.graph.edges
        assert self.graph.edges["module1", "module2"]["type"] == "imports"

    def test_remove_node(self):
        """Test removing a node from the graph."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_edge("module1", "module2", "imports")

        self.graph.remove_node("module1")

        assert "module1" not in self.graph.nodes
        assert ("module1", "module2") not in self.graph.edges

    def test_get_node(self):
        """Test retrieving a node from the graph."""
        node_data = {"type": "module", "path": "/path/to/module"}
        self.graph.add_node("module1", node_data)

        retrieved = self.graph.get_node("module1")
        assert retrieved == node_data

    def test_get_node_nonexistent(self):
        """Test retrieving a nonexistent node."""
        result = self.graph.get_node("nonexistent")
        assert result is None

    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module1", "module3", "imports")

        neighbors = self.graph.get_neighbors("module1")
        assert len(neighbors) == 2
        assert "module2" in neighbors
        assert "module3" in neighbors

    def test_get_neighbors_nonexistent(self):
        """Test getting neighbors of a nonexistent node."""
        neighbors = self.graph.get_neighbors("nonexistent")
        assert neighbors == []

    def test_has_cycle_simple(self):
        """Test cycle detection in a simple graph."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module1", "imports")

        assert self.graph.has_cycle()

    def test_has_cycle_complex(self):
        """Test cycle detection in a complex graph."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module3", "imports")
        self.graph.add_edge("module3", "module1", "imports")

        assert self.graph.has_cycle()

    def test_has_cycle_no_cycle(self):
        """Test cycle detection in a graph without cycles."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module3", "imports")

        assert not self.graph.has_cycle()

    def test_topological_sort(self):
        """Test topological sorting of the graph."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module3", "imports")

        sorted_nodes = self.graph.topological_sort()

        # Check that dependencies come before dependents
        assert sorted_nodes.index("module1") < sorted_nodes.index("module2")
        assert sorted_nodes.index("module2") < sorted_nodes.index("module3")

    def test_topological_sort_with_cycle(self):
        """Test topological sort with cycle detection."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module1", "imports")

        with pytest.raises(ValueError, match="Graph contains cycles"):
            self.graph.topological_sort()

    def test_find_cycles(self):
        """Test finding cycles in the graph."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module3", "imports")
        self.graph.add_edge("module3", "module1", "imports")

        cycles = self.graph.find_cycles()

        assert len(cycles) > 0
        # Check that at least one cycle contains all three modules
        assert any(len(cycle) == 3 for cycle in cycles)

    def test_find_cycles_no_cycles(self):
        """Test finding cycles in a graph without cycles."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_edge("module1", "module2", "imports")

        cycles = self.graph.find_cycles()
        assert cycles == []

    def test_get_dependency_path(self):
        """Test getting dependency path between nodes."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module3", "imports")

        path = self.graph.get_dependency_path("module1", "module3")
        assert path == ["module1", "module2", "module3"]

    def test_get_dependency_path_no_path(self):
        """Test getting dependency path when no path exists."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")

        path = self.graph.get_dependency_path("module1", "module3")
        assert path is None

    def test_get_reverse_dependencies(self):
        """Test getting reverse dependencies of a node."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module3", "module2", "imports")

        reverse_deps = self.graph.get_reverse_dependencies("module2")
        assert len(reverse_deps) == 2
        assert "module1" in reverse_deps
        assert "module3" in reverse_deps

    def test_get_dependency_tree(self):
        """Test getting dependency tree for a node."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_node("module4", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module1", "module3", "imports")
        self.graph.add_edge("module2", "module4", "imports")

        tree = self.graph.get_dependency_tree("module1")

        assert "module1" in tree
        assert "module2" in tree["module1"]
        assert "module3" in tree["module1"]
        assert "module4" in tree["module1"]["module2"]

    def test_analyze_dependency_metrics(self):
        """Test analyzing dependency metrics."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module1", "module3", "imports")
        self.graph.add_edge("module2", "module3", "imports")

        metrics = self.graph.analyze_dependency_metrics()

        assert "total_nodes" in metrics
        assert "total_edges" in metrics
        assert "average_dependencies" in metrics
        assert "max_dependencies" in metrics

        assert metrics["total_nodes"] == 3
        assert metrics["total_edges"] == 3

    def test_export_to_dot(self):
        """Test exporting graph to DOT format."""
        self.graph.add_node("module1", {"type": "module"})
        self.graph.add_node("module2", {"type": "module"})
        self.graph.add_edge("module1", "module2", "imports")

        dot_content = self.graph.export_to_dot()

        assert "digraph" in dot_content
        assert "module1" in dot_content
        assert "module2" in dot_content
        assert "module1 -> module2" in dot_content

    def test_export_to_json(self):
        """Test exporting graph to JSON format."""
        self.graph.add_node("module1", {"type": "module"})
        self.graph.add_node("module2", {"type": "module"})
        self.graph.add_edge("module1", "module2", "imports")

        json_content = self.graph.export_to_json()

        assert "nodes" in json_content
        assert "edges" in json_content
        assert len(json_content["nodes"]) == 2
        assert len(json_content["edges"]) == 1

    def test_clear_graph(self):
        """Test clearing the entire graph."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_edge("module1", "module2", "imports")

        self.graph.clear()

        assert len(self.graph.nodes) == 0
        assert len(self.graph.edges) == 0

    def test_get_subgraph(self):
        """Test getting a subgraph containing specific nodes."""
        self.graph.add_node("module1", {})
        self.graph.add_node("module2", {})
        self.graph.add_node("module3", {})
        self.graph.add_edge("module1", "module2", "imports")
        self.graph.add_edge("module2", "module3", "imports")

        subgraph = self.graph.get_subgraph(["module1", "module2"])

        assert "module1" in subgraph.nodes
        assert "module2" in subgraph.nodes
        assert "module3" not in subgraph.nodes
        assert ("module1", "module2") in subgraph.edges
        assert ("module2", "module3") not in subgraph.edges
