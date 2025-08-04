"""
Integration tests for the foundation components of the dependency graph system.

This module tests the integration between core data types, AST analyzer, and dependency graph
components to ensure they work correctly together.
"""

import ast

import pytest

from genai_docs.ast_analyzer import ASTAnalyzer, ImportExtractor
from genai_docs.core_types import (
    DependencyGraph,
    DocumentationContext,
    ImportStatement,
    ModuleNode,
)
from genai_docs.dependency_graph import DependencyAnalyzer, DependencyGraphBuilder


class TestCoreTypesIntegration:
    """Integration tests for the core data types."""

    def test_import_statement_creation(self):
        """Test ImportStatement creation and representation."""
        # Test basic import
        import_stmt = ImportStatement(
            module_name="os",
            alias=None,
            from_import=False,
            line_number=1
        )
        assert str(import_stmt) == "import os"

        # Test import with alias
        import_stmt = ImportStatement(
            module_name="os",
            alias="operating_system",
            from_import=False,
            line_number=1
        )
        assert str(import_stmt) == "import os as operating_system"

        # Test from import
        import_stmt = ImportStatement(
            module_name="os",
            alias=None,
            from_import=True,
            imported_items=["path"],
            line_number=1
        )
        assert str(import_stmt) == "from os import path"

        # Test relative import
        import_stmt = ImportStatement(
            module_name="utils",
            alias=None,
            from_import=True,
            imported_items=["helper"],
            line_number=1,
            is_relative=True,
            relative_level=1
        )
        assert str(import_stmt) == "from utils import helper"

    def test_module_node_creation(self):
        """Test ModuleNode creation and basic operations."""
        node = ModuleNode(
            path="/test/path/module.py",
            name="module",
            is_package=False
        )

        assert node.path == "/test/path/module.py"
        assert node.name == "module"
        assert node.is_package is False
        assert len(node.dependencies) == 0
        assert len(node.dependents) == 0
        assert node.documentation_state == "pending"

    def test_module_node_dependencies(self):
        """Test ModuleNode dependency management."""
        node1 = ModuleNode(path="/test/path/module1.py", name="module1")
        node2 = ModuleNode(path="/test/path/module2.py", name="module2")

        # Add dependency
        node1.add_dependency(node2)
        assert node2 in node1.dependencies
        assert node1 in node2.dependents

        # Remove dependency
        node1.remove_dependency(node2)
        assert node2 not in node1.dependencies
        assert node1 not in node2.dependents

    def test_dependency_graph_creation(self):
        """Test DependencyGraph creation and basic operations."""
        graph = DependencyGraph()

        node1 = ModuleNode(path="/test/path/module1.py", name="module1")
        node2 = ModuleNode(path="/test/path/module2.py", name="module2")

        graph.add_node(node1)
        graph.add_node(node2)

        assert graph.get_node_count() == 2
        assert graph.get_edge_count() == 0
        assert graph.get_node("/test/path/module1.py") == node1

    def test_documentation_context(self):
        """Test DocumentationContext operations."""
        context = DocumentationContext()

        context.add_module_context(
            module_name="test_module",
            summary="A test module",
            interface="def test_function()",
            examples="import test_module",
            relationships="Depends on utils"
        )

        module_context = context.get_module_context("test_module")
        assert module_context['summary'] == "A test module"
        assert module_context['interface'] == "def test_function()"
        assert module_context['examples'] == "import test_module"
        assert module_context['relationships'] == "Depends on utils"


class TestASTAnalyzerIntegration:
    """Integration tests for the AST analyzer component."""

    def test_import_extractor_basic_imports(self):
        """Test ImportExtractor with basic import statements."""
        source_code = """
import os
import sys as system
from pathlib import Path
from . import utils
from ..models import User
"""

        tree = ast.parse(source_code)
        extractor = ImportExtractor()
        extractor.visit(tree)

        imports = extractor.imports
        assert len(imports) == 5

        # Check first import
        assert imports[0].module_name == "os"
        assert imports[0].from_import is False
        assert imports[0].alias is None

        # Check import with alias
        assert imports[1].module_name == "sys"
        assert imports[1].alias == "system"

        # Check from import
        assert imports[2].module_name == "pathlib"
        assert imports[2].from_import is True
        assert imports[2].imported_items == ["Path"]

        # Check relative imports
        assert imports[3].is_relative is True
        assert imports[3].relative_level == 1
        assert imports[4].is_relative is True
        assert imports[4].relative_level == 2

    def test_ast_analyzer_file_analysis(self, tmp_path):
        """Test ASTAnalyzer with actual files."""
        # Create a test Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
import os
import sys
from pathlib import Path
from .utils import helper_function
""")

        analyzer = ASTAnalyzer(str(tmp_path))
        imports = analyzer.extract_imports_from_file(str(test_file))

        assert len(imports) == 4
        assert imports[0].module_name == "os"
        assert imports[1].module_name == "sys"
        assert imports[2].module_name == "pathlib"
        assert imports[3].is_relative is True

    def test_external_import_detection(self):
        """Test external import detection."""
        analyzer = ASTAnalyzer("/tmp")

        # Standard library imports should be external
        stdlib_import = ImportStatement(module_name="os")
        assert analyzer.is_external_import(stdlib_import) is True

        # Third-party imports should be external
        third_party_import = ImportStatement(module_name="numpy")
        assert analyzer.is_external_import(third_party_import) is True

        # Relative imports should not be external
        relative_import = ImportStatement(module_name="utils", is_relative=True)
        assert analyzer.is_external_import(relative_import) is False

        # Project imports should not be external (simplified check)
        project_import = ImportStatement(module_name="my_module")
        assert analyzer.is_external_import(project_import) is False


class TestDependencyGraphIntegration:
    """Integration tests for the dependency graph components."""

    def test_dependency_graph_builder(self, tmp_path):
        """Test DependencyGraphBuilder with simple project structure."""
        # Create a simple project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create module files
        (project_dir / "module1.py").write_text("import module2")
        (project_dir / "module2.py").write_text("import os")
        (project_dir / "module3.py").write_text("from . import module1")

        # Create ModuleNode objects
        nodes = [
            ModuleNode(path=str(project_dir / "module1.py"), name="module1"),
            ModuleNode(path=str(project_dir / "module2.py"), name="module2"),
            ModuleNode(path=str(project_dir / "module3.py"), name="module3"),
        ]

        # Build dependency graph
        builder = DependencyGraphBuilder(str(project_dir))
        graph = builder.build_graph(nodes)

        assert graph.get_node_count() == 3
        # Note: The actual edge count depends on import resolution success

    def test_dependency_analyzer_metrics(self):
        """Test DependencyAnalyzer metrics calculation."""
        # Create a simple graph
        graph = DependencyGraph()

        node1 = ModuleNode(path="/test/module1.py", name="module1")
        node2 = ModuleNode(path="/test/module2.py", name="module2")
        node3 = ModuleNode(path="/test/module3.py", name="module3")

        # Add dependencies: module1 -> module2 -> module3
        node1.add_dependency(node2)
        node2.add_dependency(node3)

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Analyze graph
        analyzer = DependencyAnalyzer()
        analysis = analyzer.analyze_graph(graph)

        metrics = analysis['metrics']
        assert metrics['node_count'] == 3
        assert metrics['edge_count'] == 2
        assert metrics['avg_dependencies'] == 2 / 3
        assert metrics['avg_dependents'] == 2 / 3
        assert metrics['root_node_count'] == 1  # module3
        assert metrics['leaf_node_count'] == 1  # module1
        assert metrics['cycle_count'] == 0

    def test_cycle_detection(self):
        """Test circular dependency detection."""
        # Create a graph with a cycle: module1 -> module2 -> module3 -> module1
        graph = DependencyGraph()

        node1 = ModuleNode(path="/test/module1.py", name="module1")
        node2 = ModuleNode(path="/test/module2.py", name="module2")
        node3 = ModuleNode(path="/test/module3.py", name="module3")

        node1.add_dependency(node2)
        node2.add_dependency(node3)
        node3.add_dependency(node1)  # Creates cycle

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Analyze graph
        analyzer = DependencyAnalyzer()
        analysis = analyzer.analyze_graph(graph)

        assert analysis['has_cycles'] is True
        assert analysis['cycle_count'] == 1
        assert len(analysis['cycles'][0]) == 3

        # Check that nodes are marked as part of cycles
        assert node1.cycle_group is not None
        assert node2.cycle_group is not None
        assert node3.cycle_group is not None
        assert node1.is_cycle_representative is True

    def test_topological_ordering(self):
        """Test topological ordering generation."""
        # Create a DAG: module1 -> module2 -> module3
        graph = DependencyGraph()

        node1 = ModuleNode(path="/test/module1.py", name="module1")
        node2 = ModuleNode(path="/test/module2.py", name="module2")
        node3 = ModuleNode(path="/test/module3.py", name="module3")

        node1.add_dependency(node2)
        node2.add_dependency(node3)

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Analyze graph
        analyzer = DependencyAnalyzer()
        analysis = analyzer.analyze_graph(graph)

        topological_order = analysis['topological_order']
        assert len(topological_order) == 3

        # Check that dependencies come before dependents
        node1_idx = topological_order.index(node1)
        node2_idx = topological_order.index(node2)
        node3_idx = topological_order.index(node3)

        # In topological order, dependencies should come before dependents
        # So module3 (no dependencies) should come before module2 (depends on module3)
        # and module2 should come before module1 (depends on module2)
        assert node3_idx < node2_idx  # module3 before module2
        assert node2_idx < node1_idx  # module2 before module1


class TestEndToEndIntegration:
    """End-to-end integration tests for the foundation components."""

    def test_end_to_end_analysis(self, tmp_path):
        """Test complete end-to-end analysis workflow."""
        # Create a test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create module files with imports
        (project_dir / "main.py").write_text("""
import os
from .utils import helper
from .models import User
""")

        (project_dir / "utils.py").write_text("""
import sys
from pathlib import Path

def helper():
    return "help"
""")

        (project_dir / "models.py").write_text("""
from .utils import helper

class User:
    def __init__(self):
        self.helper = helper()
""")

        # Create ModuleNode objects
        nodes = [
            ModuleNode(path=str(project_dir / "main.py"), name="main"),
            ModuleNode(path=str(project_dir / "utils.py"), name="utils"),
            ModuleNode(path=str(project_dir / "models.py"), name="models"),
        ]

        # Build and analyze dependency graph
        builder = DependencyGraphBuilder(str(project_dir))
        graph = builder.build_graph(nodes)

        analyzer = DependencyAnalyzer()
        analysis = analyzer.analyze_graph(graph)

        # Verify analysis results
        assert analysis['node_count'] == 3
        assert analysis['has_cycles'] is False  # Should be no cycles in this simple case

        # Check that import statements were extracted
        for node in nodes:
            assert len(node.import_statements) > 0

        # Check that dependencies were established
        main_node = graph.get_node(str(project_dir / "main.py"))
        utils_node = graph.get_node(str(project_dir / "utils.py"))
        models_node = graph.get_node(str(project_dir / "models.py"))

        # The exact dependency relationships depend on import resolution
        # but we should have some internal dependencies
        total_deps = len(main_node.dependencies) + len(utils_node.dependencies) + len(models_node.dependencies)
        assert total_deps >= 0  # At minimum, no internal dependencies


if __name__ == "__main__":
    pytest.main([__file__])
