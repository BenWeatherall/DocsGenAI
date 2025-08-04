# Testing Strategy for Dependency Graph Documentation System

## Overview

This document outlines the comprehensive testing strategy for the enhanced GenAI Docs system with dependency graph capabilities. The testing approach ensures reliability, maintainability, and performance while validating that the system correctly handles complex dependency scenarios.

## Testing Philosophy

### 1. Testability by Design
- **Modular Components**: Each component has clear interfaces for isolated testing
- **Dependency Injection**: Allow mocking of external dependencies (LLM calls, file system)
- **Configurable Behavior**: Make behavior configurable to enable testing different scenarios
- **Observable State**: Provide ways to inspect internal state for verification

### 2. Test Pyramid Structure
- **Unit Tests (70%)**: Fast, isolated tests of individual components
- **Integration Tests (20%)**: Test component interactions with realistic data
- **End-to-End Tests (10%)**: Complete workflow tests with real projects

### 3. Quality Assurance Priorities
1. **Correctness**: Dependency analysis and ordering are 100% accurate
2. **Robustness**: System handles edge cases and errors gracefully
3. **Performance**: Acceptable performance with large codebases
4. **Maintainability**: Tests are clear, maintainable, and fast

## Test Structure and Organization

### Directory Structure

```
tests/
├── unit/                           # Unit tests
│   ├── test_ast_analyzer.py        # AST analysis tests
│   ├── test_dependency_graph.py    # Dependency graph tests
│   ├── test_doc_orchestrator.py    # Orchestrator tests
│   ├── test_context_manager.py     # Context management tests
│   ├── test_progress_tracker.py    # Progress tracking tests
│   ├── test_error_handler.py       # Error handling tests
│   └── test_visualization.py       # Visualization tests
│
├── integration/                    # Integration tests
│   ├── test_end_to_end.py         # Complete workflow tests
│   ├── test_real_projects.py      # Tests with real projects
│   ├── test_performance.py        # Performance benchmarks
│   └── test_compatibility.py      # Backward compatibility tests
│
├── fixtures/                      # Test data and fixtures
│   ├── simple_project/           # Basic linear dependencies
│   ├── circular_deps/            # Circular dependency scenarios
│   ├── complex_project/          # Real-world complex structure
│   ├── edge_cases/               # Edge case scenarios
│   ├── malformed/                # Syntax errors, missing files
│   └── performance/              # Large projects for performance testing
│
├── mocks/                         # Mock objects and helpers
│   ├── mock_llm.py               # Mock LLM responses
│   ├── mock_filesystem.py       # Mock file system
│   └── test_helpers.py           # Shared test utilities
│
└── conftest.py                   # Pytest configuration and fixtures
```

## Unit Testing Strategy

### 1. AST Analyzer Tests

```python
# tests/unit/test_ast_analyzer.py

class TestASTAnalyzer:
    """Test the AST analyzer component."""

    def test_extract_simple_imports(self):
        """Test extraction of basic import statements."""
        source = """
import os
import sys as system
from pathlib import Path
"""
        analyzer = ASTAnalyzer("/project/root")
        imports = analyzer.extract_imports(source, "/project/file.py")

        assert len(imports) == 3
        assert imports[0].module_name == "os"
        assert imports[1].module_name == "sys"
        assert imports[1].aliases == {"system": "sys"}
        assert imports[2].module_name == "pathlib"
        assert imports[2].imported_names == ["Path"]

    def test_extract_relative_imports(self):
        """Test extraction of relative import statements."""
        source = """
from . import sibling
from .. import parent
from ...grandparent import uncle
"""
        analyzer = ASTAnalyzer("/project/root")
        imports = analyzer.extract_imports(source, "/project/package/subpackage/file.py")

        assert len(imports) == 3
        assert imports[0].is_relative and imports[0].relative_level == 1
        assert imports[1].is_relative and imports[1].relative_level == 2
        assert imports[2].is_relative and imports[2].relative_level == 3

    def test_resolve_internal_imports(self):
        """Test resolution of imports to internal project files."""
        # Setup mock project structure
        project_structure = {
            "/project/root/module1.py": "# Module 1",
            "/project/root/package/__init__.py": "# Package",
            "/project/root/package/module2.py": "# Module 2"
        }

        with mock_filesystem(project_structure):
            analyzer = ASTAnalyzer("/project/root")

            # Test absolute import resolution
            import_stmt = ImportStatement(
                module_name="package.module2",
                imported_names=[],
                aliases={},
                is_from_import=False,
                is_relative=False,
                relative_level=0,
                line_number=1,
                column_offset=0
            )

            resolved = analyzer.resolve_import(import_stmt, "/project/root/module1.py")
            assert resolved is not None
            assert resolved.is_internal
            assert "/project/root/package/module2.py" in resolved.resolved_paths

    def test_handle_syntax_errors(self):
        """Test handling of files with syntax errors."""
        malformed_source = """
import os
def broken_function(
    # Missing closing parenthesis
"""
        analyzer = ASTAnalyzer("/project/root")
        result = analyzer.analyze_file_content(malformed_source, "/project/file.py")

        assert result is not None
        assert len(result.errors) > 0
        assert "syntax error" in result.errors[0].lower()

    @pytest.mark.parametrize("import_pattern,expected_count", [
        ("import os, sys, json", 3),
        ("from collections import defaultdict, Counter", 1),
        ("from . import *", 1),
        ("if True:\n    import conditional", 1),
    ])
    def test_import_pattern_extraction(self, import_pattern, expected_count):
        """Test extraction of various import patterns."""
        analyzer = ASTAnalyzer("/project/root")
        imports = analyzer.extract_imports(import_pattern, "/project/file.py")
        assert len(imports) == expected_count
```

### 2. Dependency Graph Tests

```python
# tests/unit/test_dependency_graph.py

class TestDependencyGraph:
    """Test dependency graph construction and analysis."""

    def test_simple_linear_dependencies(self):
        """Test graph construction with linear dependencies A -> B -> C."""
        # Create mock module nodes
        node_a = create_mock_module_node("a", dependencies=["b"])
        node_b = create_mock_module_node("b", dependencies=["c"])
        node_c = create_mock_module_node("c", dependencies=[])

        graph = DependencyGraph(create_mock_tree([node_a, node_b, node_c]))
        graph.build_graph()

        # Verify graph structure
        assert graph.graph.has_edge(node_a, node_b)
        assert graph.graph.has_edge(node_b, node_c)
        assert not graph.graph.has_edge(node_c, node_a)  # No cycles

        # Verify topological order
        order = graph.get_topological_order()
        assert order.index(node_c) < order.index(node_b) < order.index(node_a)

    def test_condensed_graph_creation(self):
        """Test creation of condensed graph for cycle handling."""
        # Create circular dependency: A -> B -> C -> A
        node_a = create_mock_module_node("a", dependencies=["b"])
        node_b = create_mock_module_node("b", dependencies=["c"])
        node_c = create_mock_module_node("c", dependencies=["a"])

        graph = DependencyGraph(create_mock_tree([node_a, node_b, node_c]))
        graph.build_graph()

        # Test the _create_condensed_graph method directly
        cycles = [set([node_a, node_b, node_c])]
        condensed = graph._create_condensed_graph(cycles)

        # Should have one condensed node representing the cycle
        assert len(condensed.nodes()) == 1
        cycle_node = list(condensed.nodes())[0]
        assert isinstance(cycle_node, list)
        assert set(cycle_node) == {node_a, node_b, node_c}

    def test_documentation_order_with_mixed_structure(self):
        """Test documentation order with both cycles and linear dependencies."""
        # Create structure: D -> [A -> B -> C -> A] (cycle)
        node_a = create_mock_module_node("a", dependencies=["b"])
        node_b = create_mock_module_node("b", dependencies=["c"])
        node_c = create_mock_module_node("c", dependencies=["a"])
        node_d = create_mock_module_node("d", dependencies=["a"])

        graph = DependencyGraph(create_mock_tree([node_a, node_b, node_c, node_d]))
        graph.build_graph()

        order = graph.get_documentation_order()

        # Should have cycle first, then D
        assert len(order) == 2
        assert isinstance(order[0], list)  # Cycle group
        assert set(order[0]) == {node_a, node_b, node_c}
        assert order[1] == node_d

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        # Create circular dependency: A -> B -> C -> A
        node_a = create_mock_module_node("a", dependencies=["b"])
        node_b = create_mock_module_node("b", dependencies=["c"])
        node_c = create_mock_module_node("c", dependencies=["a"])

        graph = DependencyGraph(create_mock_tree([node_a, node_b, node_c]))
        graph.build_graph()

        cycles = graph.detect_cycles()
        assert len(cycles) == 1
        assert set(cycles[0]) == {node_a, node_b, node_c}

    def test_complex_dependency_structure(self):
        """Test complex dependency structure with multiple components."""
        # Create structure:
        # A -> B, C
        # B -> D
        # C -> D, E
        # D -> (leaf)
        # E -> (leaf)
        nodes = {
            'a': create_mock_module_node("a", dependencies=["b", "c"]),
            'b': create_mock_module_node("b", dependencies=["d"]),
            'c': create_mock_module_node("c", dependencies=["d", "e"]),
            'd': create_mock_module_node("d", dependencies=[]),
            'e': create_mock_module_node("e", dependencies=[])
        }

        graph = DependencyGraph(create_mock_tree(list(nodes.values())))
        graph.build_graph()

        # Verify no cycles
        cycles = graph.detect_cycles()
        assert len(cycles) == 0

        # Verify correct ordering (leaves first)
        order = graph.get_topological_order()
        d_index = order.index(nodes['d'])
        e_index = order.index(nodes['e'])
        b_index = order.index(nodes['b'])
        c_index = order.index(nodes['c'])
        a_index = order.index(nodes['a'])

        assert d_index < b_index < a_index
        assert e_index < c_index < a_index
        assert d_index < c_index

    def test_self_dependency(self):
        """Test handling of self-dependencies (should be ignored)."""
        node_a = create_mock_module_node("a", dependencies=["a"])  # Self-dependency

        graph = DependencyGraph(create_mock_tree([node_a]))
        graph.build_graph()

        # Self-dependencies should be ignored
        assert not graph.graph.has_edge(node_a, node_a)
        assert len(list(graph.graph.nodes())) == 1
```

### 3. Documentation Orchestrator Tests

```python
# tests/unit/test_doc_orchestrator.py

class TestDocumentationOrchestrator:
    """Test the documentation orchestration logic."""

    def setup_method(self):
        """Setup for each test method."""
        self.mock_llm = MockLLMProvider()
        self.config = OrchestratorConfig(
            enable_dependency_analysis=True,
            continue_on_errors=True,
            max_retry_attempts=2
        )

    def test_simple_linear_documentation_order(self):
        """Test documentation of simple linear dependencies."""
        # Create A -> B -> C dependency chain
        nodes = create_linear_dependency_chain(["c", "b", "a"])

        orchestrator = DocumentationOrchestrator(
            create_mock_tree(nodes),
            self.config
        )

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            result = orchestrator.orchestrate_documentation()

        assert result.success
        assert result.documented_nodes == 3

        # Verify documentation order (C should be documented before B before A)
        call_order = self.mock_llm.get_call_order()
        assert call_order.index("c") < call_order.index("b") < call_order.index("a")

    def test_context_passing_between_dependencies(self):
        """Test that dependency documentation is passed as context."""
        # Create A -> B dependency where B should get A's context
        node_a = create_mock_module_node("a", dependencies=[])
        node_b = create_mock_module_node("b", dependencies=["a"])

        orchestrator = DocumentationOrchestrator(
            create_mock_tree([node_a, node_b]),
            self.config
        )

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            result = orchestrator.orchestrate_documentation()

        # Use improved verification method
        assert self.mock_llm.verify_context_passing("b", ["a"])

        # Verify the prompt structure
        b_prompt = self.mock_llm.get_prompt_for_node("b")
        assert "context from dependencies" in b_prompt.lower()
        assert "a" in b_prompt.lower()

    def test_context_summarization_length_limits(self):
        """Test that context is properly summarized when it exceeds limits."""
        # Create dependency with long documentation
        node_a = create_mock_module_node("a", dependencies=[])
        node_b = create_mock_module_node("b", dependencies=["a"])

        # Set very long response for A
        long_doc = "This is a very long documentation. " * 100  # 3700+ characters
        self.mock_llm.set_response("a", long_doc)

        # Set short context limit
        self.config.max_context_length = 200

        orchestrator = DocumentationOrchestrator(
            create_mock_tree([node_a, node_b]),
            self.config
        )

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            result = orchestrator.orchestrate_documentation()

        # Verify context was summarized
        b_prompt = self.mock_llm.get_prompt_for_node("b")
        assert len(b_prompt) > 0  # Got some context
        assert "This is a very long documentation" in b_prompt  # Got the start
        assert len(b_prompt) < len(long_doc) + 500  # Was summarized, not full length

    def test_granular_node_state_transitions(self):
        """Test detailed state transitions during documentation process."""
        node_a = create_mock_module_node("a", dependencies=[])

        orchestrator = DocumentationOrchestrator(
            create_mock_tree([node_a]),
            self.config
        )

        # Track state changes
        state_history = []
        original_set_state = orchestrator.progress_tracker.set_node_state

        def track_state_changes(node, state):
            state_history.append((node.name, state))
            return original_set_state(node, state)

        orchestrator.progress_tracker.set_node_state = track_state_changes

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            result = orchestrator.orchestrate_documentation()

        # Verify expected state transitions
        expected_states = [
            ("a", DocumentationState.READY_FOR_DOCUMENTATION),
            ("a", DocumentationState.DOCUMENTING),
            ("a", DocumentationState.COMPLETED)
        ]

        for expected_state in expected_states:
            assert expected_state in state_history

    def test_circular_dependency_documentation(self):
        """Test documentation of circular dependencies."""
        # Create A -> B -> C -> A circular dependency
        nodes = create_circular_dependency_chain(["a", "b", "c"])

        orchestrator = DocumentationOrchestrator(
            create_mock_tree(nodes),
            self.config
        )

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            result = orchestrator.orchestrate_documentation()

        assert result.success
        assert len(result.circular_dependencies) == 1
        assert len(result.circular_dependencies[0]) == 3

        # All nodes in cycle should be documented
        for node in nodes:
            assert node.documentation_state == DocumentationState.COMPLETED

    def test_error_handling_and_retry(self):
        """Test error handling and retry mechanisms."""
        node_a = create_mock_module_node("a", dependencies=[])

        # Configure mock to fail first two attempts, succeed on third
        self.mock_llm.set_failure_pattern("a", [True, True, False])

        orchestrator = DocumentationOrchestrator(
            create_mock_tree([node_a]),
            self.config
        )

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            result = orchestrator.orchestrate_documentation()

        assert result.success
        assert self.mock_llm.get_call_count("a") == 3  # Two failures + one success

    def test_progress_tracking(self):
        """Test progress tracking during documentation."""
        nodes = create_linear_dependency_chain(["c", "b", "a"])

        orchestrator = DocumentationOrchestrator(
            create_mock_tree(nodes),
            self.config
        )

        progress_updates = []

        def track_progress():
            progress_updates.append(orchestrator.progress_tracker.get_completion_percentage())

        with mock.patch('genai_docs.main.get_llm_documentation', self.mock_llm.generate):
            # Track progress at various points
            with mock.patch.object(orchestrator, '_on_node_completed', side_effect=track_progress):
                result = orchestrator.orchestrate_documentation()

        assert result.success
        assert len(progress_updates) == 3
        assert progress_updates == [33.33, 66.67, 100.0]  # Approximately
```

### 4. Context Manager Tests

```python
# tests/unit/test_context_manager.py

class TestContextManager:
    """Test context management and summarization."""

    def test_context_extraction_from_dependencies(self):
        """Test extraction of relevant context from dependency documentation."""
        # Create nodes with mock documentation
        dep_node = create_mock_module_node("dependency")
        dep_node.documentation = "This module provides utility functions for file handling..."

        target_node = create_mock_module_node("target", dependencies=["dependency"])

        context_manager = ContextManager(OrchestratorConfig())
        context_manager.cache_node_documentation(dep_node, dep_node.documentation)

        context = context_manager.get_context_for_node(target_node)

        assert "dependency" in context
        assert "utility functions" in context["dependency"]

    def test_context_summarization(self):
        """Test summarization of long documentation for context."""
        long_documentation = "This is a very long documentation " * 100  # 500+ words

        context_manager = ContextManager(OrchestratorConfig(max_context_length=100))
        summary = context_manager.create_context_summary(long_documentation)

        assert len(summary) < len(long_documentation)
        assert len(summary) <= 100
        assert "this is a very long documentation" in summary.lower()

    def test_context_caching(self):
        """Test caching of documentation and context."""
        node = create_mock_module_node("test")
        documentation = "Test documentation"

        context_manager = ContextManager(OrchestratorConfig())

        # Cache documentation
        context_manager.cache_node_documentation(node, documentation)

        # Verify it's cached
        cached = context_manager.documentation_cache.get(node)
        assert cached == documentation

        # Verify context generation uses cache
        context = context_manager.get_context_for_node(node)
        assert isinstance(context, dict)
```

## Integration Testing Strategy

### 1. End-to-End Workflow Tests

```python
# tests/integration/test_end_to_end.py

class TestEndToEndWorkflow:
    """Test complete documentation workflow with realistic projects."""

    def test_simple_project_documentation(self):
        """Test documentation of a simple project structure."""
        project_structure = {
            "main.py": "from utils import helper\nfrom config import settings",
            "utils.py": "def helper(): pass",
            "config.py": "settings = {'debug': True}"
        }

        with temporary_project(project_structure) as project_path:
            # Run the complete workflow
            module_tree = build_module_tree(project_path)
            orchestrator = DocumentationOrchestrator(module_tree, OrchestratorConfig())

            with mock_llm_provider():
                result = orchestrator.orchestrate_documentation()

            assert result.success
            assert result.documented_nodes == 3

            # Verify documentation files were created
            assert os.path.exists(os.path.join(project_path, "utils_DOCUMENTATION.md"))
            assert os.path.exists(os.path.join(project_path, "config_DOCUMENTATION.md"))
            assert os.path.exists(os.path.join(project_path, "main_DOCUMENTATION.md"))

    def test_package_structure_documentation(self):
        """Test documentation of project with package structure."""
        project_structure = {
            "main.py": "from package import module1",
            "package/__init__.py": "from .module1 import function1",
            "package/module1.py": "def function1(): pass",
            "package/module2.py": "from .module1 import function1"
        }

        with temporary_project(project_structure) as project_path:
            module_tree = build_module_tree(project_path)
            orchestrator = DocumentationOrchestrator(module_tree, OrchestratorConfig())

            with mock_llm_provider():
                result = orchestrator.orchestrate_documentation()

            assert result.success

            # Verify package documentation
            package_doc_path = os.path.join(project_path, "package", "DOCUMENTATION.md")
            assert os.path.exists(package_doc_path)

    def test_circular_dependency_project(self):
        """Test documentation of project with circular dependencies."""
        project_structure = {
            "a.py": "from b import func_b",
            "b.py": "from c import func_c",
            "c.py": "from a import func_a"
        }

        with temporary_project(project_structure) as project_path:
            module_tree = build_module_tree(project_path)
            orchestrator = DocumentationOrchestrator(module_tree, OrchestratorConfig())

            with mock_llm_provider():
                result = orchestrator.orchestrate_documentation()

            assert result.success
            assert len(result.circular_dependencies) == 1

            # All files should still be documented
            for filename in ["a", "b", "c"]:
                doc_path = os.path.join(project_path, f"{filename}_DOCUMENTATION.md")
                assert os.path.exists(doc_path)
```

### 2. Real Project Tests

```python
# tests/integration/test_real_projects.py

class TestRealProjects:
    """Test with real-world Python projects."""

    @pytest.mark.slow
    def test_requests_library_analysis(self):
        """Test dependency analysis on the requests library."""
        # Use a known open-source project for testing
        with clone_repository("https://github.com/psf/requests.git") as repo_path:
            module_tree = build_module_tree(repo_path)

            # Just test dependency analysis, not full documentation
            graph = DependencyGraph(module_tree)
            graph.build_graph()

            assert len(graph.graph.nodes()) > 10  # Should have many modules
            cycles = graph.detect_cycles()
            # Note: We expect some cycles in real projects

    @pytest.mark.slow
    def test_flask_application_structure(self):
        """Test analysis of a typical Flask application structure."""
        flask_structure = create_typical_flask_structure()

        with temporary_project(flask_structure) as project_path:
            module_tree = build_module_tree(project_path)
            orchestrator = DocumentationOrchestrator(module_tree, OrchestratorConfig())

            with mock_llm_provider():
                result = orchestrator.orchestrate_documentation()

            assert result.success
            # Flask apps typically have some circular dependencies
            assert result.documented_nodes > 5
```

### 3. Performance Tests

```python
# tests/integration/test_performance.py

class TestPerformance:
    """Performance benchmarks and stress tests."""

    @pytest.mark.performance
    def test_large_project_performance(self):
        """Test performance with a large project (1000+ files)."""
        large_project = generate_large_project_structure(num_files=1000)

        with temporary_project(large_project) as project_path:
            start_time = time.time()

            module_tree = build_module_tree(project_path)
            graph = DependencyGraph(module_tree)
            graph.build_graph()

            analysis_time = time.time() - start_time

            # Should complete dependency analysis in reasonable time
            assert analysis_time < 30  # 30 seconds max
            assert len(graph.graph.nodes()) == 1000

    @pytest.mark.performance
    def test_memory_usage_large_project(self):
        """Test memory usage doesn't grow excessively."""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create and analyze large project
        large_project = generate_large_project_structure(num_files=500)

        with temporary_project(large_project) as project_path:
            module_tree = build_module_tree(project_path)
            orchestrator = DocumentationOrchestrator(module_tree, OrchestratorConfig())

            # Don't actually call LLM, just test memory of analysis
            graph = DependencyGraph(module_tree)
            graph.build_graph()

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (< 100MB for 500 files)
            assert memory_increase < 100 * 1024 * 1024
```

## Test Fixtures and Utilities

### 1. Project Structure Fixtures

```python
# tests/fixtures/project_generators.py

def create_simple_linear_project():
    """Create a simple project with linear dependencies."""
    return {
        "main.py": """
from processor import process_data
from config import get_config

def main():
    config = get_config()
    result = process_data(config)
    return result
""",
        "processor.py": """
from utils import validate_input

def process_data(config):
    if validate_input(config):
        return "processed"
    return "error"
""",
        "utils.py": """
def validate_input(data):
    return data is not None
""",
        "config.py": """
def get_config():
    return {"setting": "value"}
"""
    }

def create_circular_dependency_project():
    """Create a project with circular dependencies."""
    return {
        "models.py": """
from views import render_model

class User:
    def render(self):
        return render_model(self)
""",
        "views.py": """
from controllers import get_user_controller

def render_model(model):
    controller = get_user_controller()
    return controller.format(model)
""",
        "controllers.py": """
from models import User

def get_user_controller():
    class UserController:
        def format(self, user):
            return f"User: {user}"
    return UserController()
"""
    }

def create_complex_package_structure():
    """Create a complex project with nested packages."""
    return {
        "main.py": "from app import create_app",
        "app/__init__.py": "from .factory import create_app",
        "app/factory.py": "from .models import User\nfrom .views import api",
        "app/models/__init__.py": "from .user import User",
        "app/models/user.py": "class User: pass",
        "app/views/__init__.py": "from .api import api",
        "app/views/api.py": "from ..models import User",
        "app/utils/__init__.py": "",
        "app/utils/helpers.py": "def helper(): pass"
    }
```

### 2. Mock Objects

```python
# tests/mocks/mock_llm.py

class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self):
        self.call_history = []
        self.prompt_history = []  # Store full prompts for analysis
        self.responses = {}
        self.failure_patterns = {}
        self.call_counts = {}
        self.node_metadata = {}  # Store extracted metadata for verification

    def generate(self, prompt):
        """Mock LLM documentation generation."""
        # Store full prompt for analysis
        self.prompt_history.append(prompt)

        # Extract node information more robustly
        node_info = self._extract_node_info(prompt)
        node_name = node_info['name']

        self.call_history.append(node_name)
        self.call_counts[node_name] = self.call_counts.get(node_name, 0) + 1
        self.node_metadata[node_name] = node_info

        # Check if this call should fail
        if self._should_fail(node_name):
            raise Exception(f"Mock LLM failure for {node_name}")

        # Return mock documentation
        return self.responses.get(node_name, self._generate_default_response(node_info))

    def set_response(self, node_name, response):
        """Set mock response for a specific node."""
        self.responses[node_name] = response

    def set_failure_pattern(self, node_name, pattern):
        """Set failure pattern for a node (list of booleans)."""
        self.failure_patterns[node_name] = pattern

    def get_call_order(self):
        """Get the order in which nodes were called."""
        return self.call_history

    def get_call_count(self, node_name):
        """Get number of calls for a specific node."""
        return self.call_counts.get(node_name, 0)

    def get_prompt_for_node(self, node_name):
        """Get the last prompt used for a specific node."""
        for i, prompt in enumerate(reversed(self.prompt_history)):
            if node_name in self._extract_node_info(prompt)['name']:
                return prompt
        return None

    def verify_context_passing(self, node_name, expected_dependencies):
        """Verify that a node received context from expected dependencies."""
        node_info = self.node_metadata.get(node_name, {})
        return (node_info.get('has_dependencies', False) and
                all(dep in str(node_info.get('dependency_context', []))
                    for dep in expected_dependencies))

    def get_documentation_quality_metrics(self):
        """Get metrics about the quality of generated documentation."""
        metrics = {
            'total_calls': len(self.call_history),
            'unique_nodes': len(set(self.call_history)),
            'avg_prompt_length': sum(len(p) for p in self.prompt_history) / len(self.prompt_history) if self.prompt_history else 0,
            'nodes_with_context': sum(1 for info in self.node_metadata.values() if info.get('has_dependencies')),
            'context_ratio': 0
        }

        if metrics['unique_nodes'] > 0:
            metrics['context_ratio'] = metrics['nodes_with_context'] / metrics['unique_nodes']

        return metrics

    def _extract_node_info(self, prompt):
        """
        Extract node information from documentation prompt more robustly.

        Returns a dictionary with node metadata for testing verification.
        """
        import re

        node_info = {
            'name': 'unknown',
            'type': 'unknown',
            'has_dependencies': False,
            'dependency_context': [],
            'path': None
        }

        lines = prompt.split('\n')

        # Extract node name and type
        for line in lines:
            line_lower = line.lower()

            # Look for module/package declarations
            if 'module' in line_lower or 'package' in line_lower:
                # Extract name from various patterns
                patterns = [
                    r"module[:\s]+['\"]([^'\"]+)['\"]",
                    r"package[:\s]+['\"]([^'\"]+)['\"]",
                    r"documenting[:\s]+['\"]([^'\"]+)['\"]",
                    r"['\"]([^'\"]+)['\"][:\s]+(?:module|package)",
                ]

                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        node_info['name'] = match.group(1)
                        break

                # Determine type
                if 'package' in line_lower:
                    node_info['type'] = 'package'
                elif 'module' in line_lower:
                    node_info['type'] = 'module'

            # Check for dependency context
            if 'context from dependencies' in line_lower:
                node_info['has_dependencies'] = True

            # Extract dependency names
            if '###' in line and any(dep_word in line_lower for dep_word in ['import', 'dependency', 'depends']):
                dep_match = re.search(r'###\s*([^\n]+)', line)
                if dep_match:
                    node_info['dependency_context'].append(dep_match.group(1).strip())

        return node_info

    def _generate_default_response(self, node_info):
        """Generate a realistic default response based on node information."""
        node_name = node_info['name']
        node_type = node_info['type']

        if node_type == 'package':
            response = f"""# {node_name} Package

This package provides functionality for {node_name.replace('_', ' ')}.

## Overview

The {node_name} package contains modules and subpackages that work together to provide
comprehensive {node_name.replace('_', ' ')} capabilities.

## Key Components

- Core functionality for {node_name.replace('_', ' ')} operations
- Utilities and helper functions
- Configuration and setup modules
"""
        else:
            response = f"""# {node_name} Module

This module provides {node_name.replace('_', ' ')} functionality.

## Purpose

The {node_name} module is responsible for handling {node_name.replace('_', ' ')} operations
and integrating with other system components.

## Key Functions

- Primary {node_name.replace('_', ' ')} processing
- Data validation and transformation
- Integration with dependent modules
"""

        # Add dependency context if present
        if node_info['has_dependencies'] and node_info['dependency_context']:
            response += f"""

## Dependencies

This module builds upon the following dependencies:
{chr(10).join(f"- {dep}" for dep in node_info['dependency_context'])}
"""

        return response

    def _should_fail(self, node_name):
        """Check if this call should fail based on failure pattern."""
        if node_name not in self.failure_patterns:
            return False

        pattern = self.failure_patterns[node_name]
        call_count = self.call_counts.get(node_name, 1)

        if call_count <= len(pattern):
            return pattern[call_count - 1]

        return False
```

### 3. Test Utilities

```python
# tests/mocks/test_helpers.py

@contextmanager
def temporary_project(structure):
    """Create a temporary project with given structure."""
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    try:
        # Create files and directories
        for file_path, content in structure.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'w') as f:
                f.write(content)

        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)

@contextmanager
def mock_llm_provider():
    """Context manager for mocking LLM provider."""
    mock_provider = MockLLMProvider()

    with mock.patch('genai_docs.main.get_llm_documentation', mock_provider.generate):
        yield mock_provider

def create_mock_module_node(name, dependencies=None, is_package=False):
    """Create a mock ModuleNode for testing."""
    node = ModuleNode(
        path=f"/mock/project/{name}{'/' if is_package else '.py'}",
        name=name,
        is_package=is_package
    )

    if dependencies:
        node.dependencies = dependencies

    return node

def assert_documentation_quality(documentation):
    """Assert that generated documentation meets quality standards."""
    assert len(documentation) > 50  # Minimum length
    assert "purpose" in documentation.lower() or "functionality" in documentation.lower()
    assert not documentation.startswith("Error:")
```

## Continuous Integration and Testing Pipeline

### 1. Test Automation

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e .[dev]
        pip install pytest pytest-cov pytest-mock

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=genai_docs

    - name: Run integration tests
      run: pytest tests/integration/ -v -m "not slow and not performance"

    - name: Run performance tests (on main branch only)
      if: github.ref == 'refs/heads/main'
      run: pytest tests/integration/ -v -m performance
```

### 2. Code Quality Checks

```yaml
  quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install ruff mypy

    - name: Lint and format checking
      run: |
        ruff check genai_docs/
        ruff format --check genai_docs/

    - name: Type checking
      run: mypy genai_docs/
```

## Success Metrics and Quality Gates

### 1. Test Coverage Requirements
- **Unit Tests**: >90% code coverage
- **Integration Tests**: >80% workflow coverage
- **Critical Paths**: 100% coverage for dependency analysis and ordering

### 2. Performance Benchmarks
- **Small Projects** (<50 files): <5 seconds total time
- **Medium Projects** (50-500 files): <30 seconds total time
- **Large Projects** (500+ files): <2 minutes analysis time

### 3. Quality Gates
- All tests must pass before merge
- No decrease in test coverage
- Performance tests must not regress by >10%
- Memory usage must remain within acceptable bounds

### 4. Reliability Metrics
- **Error Handling**: 100% of error conditions must be tested
- **Edge Cases**: All identified edge cases must have tests
- **Backward Compatibility**: Existing functionality must not break

## Maintenance and Evolution

### 1. Test Maintenance Strategy
- Regular review and update of test fixtures
- Performance baseline updates as system evolves
- Addition of new test scenarios as edge cases are discovered

### 2. Test Data Management
- Version control of test fixtures
- Automated generation of large test datasets
- Regular cleanup of obsolete test data

### 3. Monitoring and Alerting
- Track test execution times for performance regression detection
- Monitor test reliability and flakiness
- Alert on coverage decreases

---

*This testing strategy provides comprehensive coverage for the dependency graph documentation system, ensuring reliability, maintainability, and performance while supporting confident development and deployment.*
