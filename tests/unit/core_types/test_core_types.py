"""
Unit tests for the core types module.

This module tests the core data structures and types used
throughout the documentation generation system.
"""

from genai_docs.core_types import (
    DependencyGraph,
    DocumentationContext,
    ImportStatement,
    ModuleNode,
)


class TestModuleNode:
    """Test the ModuleNode class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.node = ModuleNode(
            name="test_module", path="/path/to/test_module.py", is_package=False
        )

    def test_module_node_initialization(self):
        """Test ModuleNode initialization."""
        assert self.node.name == "test_module"
        assert self.node.path == "/path/to/test_module.py"
        assert not self.node.is_package
        assert self.node.children == []
        assert self.node.content is None
        assert self.node.documentation is None

    def test_module_node_package_initialization(self):
        """Test ModuleNode initialization for packages."""
        package_node = ModuleNode(
            name="test_package", path="/path/to/test_package", is_package=True
        )

        assert package_node.name == "test_package"
        assert package_node.is_package
        assert package_node.children == []

    def test_add_child(self):
        """Test adding a child node."""
        child_node = ModuleNode(
            name="child_module", path="/path/to/child_module.py", is_package=False
        )

        self.node.add_child(child_node)

        assert len(self.node.children) == 1
        assert self.node.children[0] == child_node

    def test_add_dependency(self):
        """Test adding a dependency."""
        dep_node = ModuleNode(
            name="dependency_module",
            path="/path/to/dependency_module.py",
            is_package=False,
        )

        self.node.add_dependency(dep_node)

        assert len(self.node.dependencies) == 1
        assert self.node.dependencies[0] == dep_node
        assert len(dep_node.dependents) == 1
        assert dep_node.dependents[0] == self.node

    def test_remove_dependency(self):
        """Test removing a dependency."""
        dep_node = ModuleNode(
            name="dependency_module",
            path="/path/to/dependency_module.py",
            is_package=False,
        )

        self.node.add_dependency(dep_node)
        self.node.remove_dependency(dep_node)

        assert len(self.node.dependencies) == 0
        assert len(dep_node.dependents) == 0

    def test_get_all_dependencies(self):
        """Test getting all dependencies recursively."""
        dep1 = ModuleNode(path="/path/to/dep1.py", name="dep1", is_package=False)
        dep2 = ModuleNode(path="/path/to/dep2.py", name="dep2", is_package=False)

        dep1.add_dependency(dep2)
        self.node.add_dependency(dep1)

        all_deps = self.node.get_all_dependencies()

        assert len(all_deps) == 2
        assert dep1 in all_deps
        assert dep2 in all_deps

    def test_get_all_dependents(self):
        """Test getting all dependents recursively."""
        dep1 = ModuleNode(path="/path/to/dep1.py", name="dep1", is_package=False)
        dep2 = ModuleNode(path="/path/to/dep2.py", name="dep2", is_package=False)

        dep1.add_dependency(self.node)
        dep2.add_dependency(dep1)

        all_deps = self.node.get_all_dependents()

        assert len(all_deps) == 2
        assert dep1 in all_deps
        assert dep2 in all_deps

    def test_is_leaf(self):
        """Test checking if node is a leaf."""
        assert self.node.is_leaf()

        child_node = ModuleNode(
            name="child_module", path="/path/to/child_module.py", is_package=False
        )
        self.node.add_child(child_node)

        assert not self.node.is_leaf()
        assert child_node.is_leaf()

    def test_is_leaf_module(self):
        """Test checking if node is a leaf module."""
        assert self.node.is_leaf_module()

        # Package with children is not a leaf module
        package_node = ModuleNode(
            name="test_package", path="/path/to/test_package", is_package=True
        )
        child_node = ModuleNode(
            name="child_module", path="/path/to/child_module.py", is_package=False
        )
        package_node.add_child(child_node)

        assert not package_node.is_leaf_module()
        assert child_node.is_leaf_module()

    def test_get_file_path(self):
        """Test getting file path."""
        file_path = self.node.get_file_path()
        assert str(file_path) == "/path/to/test_module.py"

        # Test package path
        package_node = ModuleNode(
            name="test_package", path="/path/to/test_package", is_package=True
        )
        package_path = package_node.get_file_path()
        assert str(package_path) == "/path/to/test_package/__init__.py"

    def test_get_module_name(self):
        """Test getting module name."""
        assert self.node.get_module_name() == "test_module"

        # Test root node
        root_node = ModuleNode(name="root_project", path="/path/to/root", is_root=True)
        assert root_node.get_module_name() == "root_project"

    def test_repr_representation(self):
        """Test repr representation of node."""
        repr_str = repr(self.node)
        assert "ModuleNode" in repr_str
        assert "test_module" in repr_str
        assert "deps=0" in repr_str


class TestImportStatement:
    """Test the ImportStatement class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.import_stmt = ImportStatement(
            module_name="test_module",
            alias="test_alias",
            from_import=True,
            imported_items=["item1", "item2"],
            line_number=10,
            is_relative=False,
            relative_level=0,
        )

    def test_import_statement_initialization(self):
        """Test ImportStatement initialization."""
        assert self.import_stmt.module_name == "test_module"
        assert self.import_stmt.alias == "test_alias"
        assert self.import_stmt.from_import
        assert self.import_stmt.imported_items == ["item1", "item2"]
        assert self.import_stmt.line_number == 10
        assert not self.import_stmt.is_relative
        assert self.import_stmt.relative_level == 0

    def test_import_statement_repr(self):
        """Test ImportStatement string representation."""
        repr_str = repr(self.import_stmt)
        assert "from test_module import item1, item2" in repr_str

    def test_import_statement_absolute_import(self):
        """Test absolute import statement."""
        import_stmt = ImportStatement(
            module_name="os", from_import=False, line_number=1
        )
        repr_str = repr(import_stmt)
        assert "import os" in repr_str

    def test_import_statement_with_alias(self):
        """Test import statement with alias."""
        import_stmt = ImportStatement(
            module_name="os", alias="operating_system", from_import=False, line_number=1
        )
        repr_str = repr(import_stmt)
        assert "import os as operating_system" in repr_str


class TestDependencyGraph:
    """Test the DependencyGraph class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.graph = DependencyGraph()

    def test_dependency_graph_initialization(self):
        """Test DependencyGraph initialization."""
        assert len(self.graph.nodes) == 0
        assert self.graph.root_node is None
        assert len(self.graph.cycles) == 0
        assert len(self.graph.topological_order) == 0

    def test_add_node(self):
        """Test adding a node to the graph."""
        node = ModuleNode(path="/path/to/module.py", name="test_module")
        self.graph.add_node(node)

        assert len(self.graph.nodes) == 1
        assert self.graph.get_node("/path/to/module.py") == node

    def test_get_all_nodes(self):
        """Test getting all nodes from the graph."""
        node1 = ModuleNode(path="/path/to/module1.py", name="module1")
        node2 = ModuleNode(path="/path/to/module2.py", name="module2")

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        all_nodes = self.graph.get_all_nodes()
        assert len(all_nodes) == 2
        assert node1 in all_nodes
        assert node2 in all_nodes

    def test_get_leaf_nodes(self):
        """Test getting leaf nodes from the graph."""
        node1 = ModuleNode(path="/path/to/module1.py", name="module1")
        node2 = ModuleNode(path="/path/to/module2.py", name="module2")

        # Add dependency relationship
        node1.add_dependency(node2)

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        leaf_nodes = self.graph.get_leaf_nodes()
        assert len(leaf_nodes) == 1
        assert node2 in leaf_nodes  # node2 has no dependencies

    def test_get_root_nodes(self):
        """Test getting root nodes from the graph."""
        node1 = ModuleNode(path="/path/to/module1.py", name="module1")
        node2 = ModuleNode(path="/path/to/module2.py", name="module2")

        # Add dependency relationship
        node1.add_dependency(node2)

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        root_nodes = self.graph.get_root_nodes()
        assert len(root_nodes) == 1
        assert node1 in root_nodes  # node1 has no dependents

    def test_has_cycles(self):
        """Test cycle detection."""
        assert not self.graph.has_cycles()

        self.graph.cycles = [[ModuleNode(path="/path/to/module.py", name="module")]]
        assert self.graph.has_cycles()

    def test_get_node_count(self):
        """Test getting node count."""
        assert self.graph.get_node_count() == 0

        node1 = ModuleNode(path="/path/to/module1.py", name="module1")
        node2 = ModuleNode(path="/path/to/module2.py", name="module2")

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        assert self.graph.get_node_count() == 2

    def test_get_edge_count(self):
        """Test getting edge count."""
        assert self.graph.get_edge_count() == 0

        node1 = ModuleNode(path="/path/to/module1.py", name="module1")
        node2 = ModuleNode(path="/path/to/module2.py", name="module2")

        # Add dependency relationship
        node1.add_dependency(node2)

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        assert self.graph.get_edge_count() == 1

    def test_clear_analysis(self):
        """Test clearing analysis results."""
        node = ModuleNode(path="/path/to/module.py", name="module")
        node.cycle_group = [node]
        node.is_cycle_representative = True

        self.graph.add_node(node)
        self.graph.cycles = [[node]]
        self.graph.topological_order = [node]

        self.graph.clear_analysis()

        assert len(self.graph.cycles) == 0
        assert len(self.graph.topological_order) == 0
        assert node.cycle_group is None
        assert not node.is_cycle_representative

    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.graph)
        assert "DependencyGraph" in repr_str
        assert "nodes=0" in repr_str
        assert "edges=0" in repr_str
        assert "cycles=0" in repr_str


class TestDocumentationContext:
    """Test the DocumentationContext class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.context = DocumentationContext()

    def test_documentation_context_initialization(self):
        """Test DocumentationContext initialization."""
        assert len(self.context.module_summaries) == 0
        assert len(self.context.interface_descriptions) == 0
        assert len(self.context.usage_examples) == 0
        assert len(self.context.relationships) == 0

    def test_add_module_context(self):
        """Test adding module context."""
        self.context.add_module_context(
            "test_module",
            "Test summary",
            "Test interface",
            "Test examples",
            "Test relationships",
        )

        assert self.context.module_summaries["test_module"] == "Test summary"
        assert self.context.interface_descriptions["test_module"] == "Test interface"
        assert self.context.usage_examples["test_module"] == "Test examples"
        assert self.context.relationships["test_module"] == "Test relationships"

    def test_get_module_context(self):
        """Test getting module context."""
        self.context.add_module_context("test_module", "Test summary", "Test interface")

        context = self.context.get_module_context("test_module")

        assert context["summary"] == "Test summary"
        assert context["interface"] == "Test interface"
        assert context["examples"] == ""
        assert context["relationships"] == ""

    def test_get_dependency_context_string(self):
        """Test getting dependency context string."""
        # Create a mock dependency
        dep_node = ModuleNode(path="/path/to/dep.py", name="dependency_module")
        dep_node.content = "def test_function(): pass"

        # Add context for the dependency
        self.context.add_module_context(
            "dependency_module", "Dependency summary", "Dependency interface"
        )

        context_string = self.context.get_dependency_context_string([dep_node])

        assert "dependency_module" in context_string
        assert "Dependency summary" in context_string
        assert "Dependency interface" in context_string

    def test_get_dependency_context_string_empty(self):
        """Test getting dependency context string with no dependencies."""
        context_string = self.context.get_dependency_context_string([])
        assert context_string == ""

    def test_repr(self):
        """Test string representation."""
        self.context.add_module_context("test_module", "Test summary")

        repr_str = repr(self.context)
        assert "DocumentationContext" in repr_str
        assert "modules=1" in repr_str
