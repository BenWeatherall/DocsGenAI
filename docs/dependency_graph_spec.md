# Dependency Graph System Specification

## Overview

The dependency graph system is the core component that analyzes Python file dependencies and provides dependency-aware ordering for documentation generation.

## Core Components

### 1. DependencyGraph Class

```python
class DependencyGraph:
    """
    Main class for managing file-level dependency analysis and graph operations.
    """

    def __init__(self, module_tree_root: ModuleNode, ast_analyzer: Optional[ASTAnalyzer] = None):
        self.root = module_tree_root
        self.graph = nx.DiGraph()  # NetworkX directed graph
        self.ast_analyzer = ast_analyzer or ASTAnalyzer(str(module_tree_root.path))
        self.resolution_cache = {}
        self.cycles = []

    def build_graph(self) -> None:
        """Build the complete dependency graph from the module tree."""

    def get_topological_order(self) -> List[ModuleNode]:
        """Return nodes in topological order for documentation."""

    def detect_cycles(self) -> List[List[ModuleNode]]:
        """Detect and return circular dependencies."""

    def get_documentation_order(self) -> List[Union[ModuleNode, List[ModuleNode]]]:
        """
        Return documentation order, grouping cycles together.

        This is the authoritative method for determining documentation order.
        The orchestrator should use this method rather than implementing its own ordering logic.

        Returns:
            List where each element is either:
            - A single ModuleNode (for non-cyclic nodes)
            - A List[ModuleNode] (for nodes in circular dependencies)
        """

    def visualize(self, output_path: str = None) -> str:
        """Generate visual representation of the dependency graph."""
```

### 2. ASTAnalyzer Class

```python
class ASTAnalyzer:
    """
    Analyzes Python source code using AST to extract import statements.
    """

    def __init__(self):
        self.import_patterns = {}

    def extract_imports(self, source_code: str, file_path: str) -> List[ImportStatement]:
        """Extract all import statements from Python source code."""

    def resolve_import(self, import_stmt: ImportStatement, current_file: str,
                      project_root: str) -> Optional[str]:
        """Resolve an import statement to an actual file path."""

    def analyze_file(self, file_path: str) -> FileAnalysis:
        """Analyze a single Python file for dependencies."""
```

### 3. Data Structures

```python
@dataclass
class ImportStatement:
    """Represents a single import statement."""
    module_name: str
    imported_names: List[str]
    is_relative: bool
    level: int  # For relative imports
    line_number: int
    is_from_import: bool
    alias: Optional[str] = None

@dataclass
class FileAnalysis:
    """Results of analyzing a single file."""
    file_path: str
    imports: List[ImportStatement]
    resolved_dependencies: List[str]
    unresolved_imports: List[ImportStatement]
    errors: List[str]

@dataclass
class DependencyEdge:
    """Represents a dependency relationship between two files."""
    source: str  # File that has the import
    target: str  # File that is imported
    import_statements: List[ImportStatement]
    edge_type: str  # 'direct', 'transitive', 'circular'
```

## Algorithm Specifications

### 1. Dependency Analysis Algorithm

```
FOR each ModuleNode in the tree:
    1. Read the source code
    2. Parse with AST to extract import statements
    3. For each import statement:
        a. Resolve to actual file path using Python's import resolution rules
        b. If resolved to internal project file, add dependency edge
        c. If unresolved, log as external dependency
    4. Add node and edges to NetworkX graph
    5. Store analysis results in ModuleNode

AFTER all files analyzed:
    1. Detect cycles using NetworkX algorithms
    2. Generate topological ordering
    3. Handle cycles by grouping into documentation units
```

### 2. Import Resolution Algorithm

```python
def resolve_import(import_name, current_file, project_root):
    """
    Replicate Python's import resolution logic for project files.

    Algorithm:
    1. Handle relative imports using current file's package context
    2. Search sys.path equivalent (project structure)
    3. Check for __init__.py files to identify packages
    4. Handle namespace packages (PEP 420)
    5. Return resolved file path or None if external/unresolved
    """
```

### 3. Topological Sorting with Cycle Handling

```python
def get_documentation_order(self) -> List[Union[ModuleNode, List[ModuleNode]]]:
    """
    Return documentation order handling cycles appropriately.

    This method is the single source of truth for documentation ordering.
    It encapsulates all the complexity of topological sorting and cycle handling.

    Algorithm:
    1. Detect strongly connected components (cycles)
    2. Create condensed graph where each SCC is a single node
    3. Perform topological sort on condensed graph
    4. For each SCC with multiple nodes, return as a group
    5. Return mixed list of individual nodes and cycle groups

    Returns:
        List where each element is either:
        - A single ModuleNode (for nodes with no cycles)
        - A List[ModuleNode] (for nodes in circular dependencies)
    """

    # Detect cycles using strongly connected components
    cycles = list(nx.strongly_connected_components(self.graph))

    if all(len(cycle) == 1 for cycle in cycles):
        # No actual cycles (all SCCs are single nodes)
        return list(nx.topological_sort(self.graph))

    # Handle cycles by creating condensed graph
    condensed = self._create_condensed_graph(cycles)
    condensed_order = list(nx.topological_sort(condensed))

    # Expand condensed nodes back to original format
    documentation_order = []
    for condensed_node in condensed_order:
        if isinstance(condensed_node, list) and len(condensed_node) > 1:
            # It's a cycle group
            documentation_order.append(condensed_node)
        else:
            # It's a single node (extract from list if needed)
            if isinstance(condensed_node, list):
                documentation_order.append(condensed_node[0])
            else:
                documentation_order.append(condensed_node)

    return documentation_order

def _create_condensed_graph(self, cycles: List[Set[ModuleNode]]) -> nx.DiGraph:
    """Create a condensed graph where cycles are collapsed into single nodes."""
    condensed_graph = nx.DiGraph()
    node_to_cycle = {}  # Map individual nodes to their cycle group

    # Create mapping and add cycle groups as nodes
    for i, cycle in enumerate(cycles):
        if len(cycle) > 1:
            # Actual cycle - create group
            cycle_list = list(cycle)
            condensed_graph.add_node(cycle_list)
            for node in cycle:
                node_to_cycle[node] = cycle_list
        else:
            # Single node - add directly
            node = list(cycle)[0]
            condensed_graph.add_node(node)
            node_to_cycle[node] = node

    # Add edges between condensed nodes
    for source, target in self.graph.edges():
        condensed_source = node_to_cycle[source]
        condensed_target = node_to_cycle[target]

        # Don't add self-loops for cycles
        if condensed_source != condensed_target:
            condensed_graph.add_edge(condensed_source, condensed_target)

    return condensed_graph
```

## Integration with ModuleNode

### Enhanced ModuleNode Fields

```python
class ModuleNode:
    # Existing fields...

    # New dependency-related fields
    dependencies: List['ModuleNode'] = field(default_factory=list)
    dependents: List['ModuleNode'] = field(default_factory=list)
    import_statements: List[ImportStatement] = field(default_factory=list)
    resolved_imports: Dict[str, str] = field(default_factory=dict)
    unresolved_imports: List[str] = field(default_factory=list)

    # Documentation state tracking
    documentation_state: str = "pending"  # pending/analyzing/documenting/completed/error
    dependency_context: Dict[str, str] = field(default_factory=dict)  # Cached dependency docs

    # Cycle handling
    cycle_group: Optional[List['ModuleNode']] = None
    is_cycle_representative: bool = False
```

### ModuleNode Methods

```python
def add_dependency(self, dependency_node: 'ModuleNode', import_statements: List[ImportStatement]):
    """Add a dependency relationship with import context."""

def get_dependency_documentation(self) -> Dict[str, str]:
    """Get documentation from all dependencies for context passing."""

def is_ready_for_documentation(self) -> bool:
    """Check if all dependencies are documented and node is ready."""

def mark_documentation_complete(self):
    """Mark this node as completely documented."""
```

## Error Handling and Edge Cases

### 1. Unresolvable Imports

```python
# Handle cases where imports cannot be resolved:
# - External libraries (numpy, requests, etc.)
# - Dynamic imports (importlib.import_module with variables)
# - Conditional imports
# - Missing files

# Strategy: Log but don't fail, continue with partial dependency graph
```

### 2. Circular Dependencies

```python
# Detection: Use NetworkX strongly connected components
# Handling:
#   1. Group cycle nodes together for documentation
#   2. Document cycle as a unit with explanation
#   3. Provide clear reporting to user
#   4. Allow manual override of cycle breaking
```

### 3. Complex Import Patterns

```python
# Relative imports: from ..parent import module
# Star imports: from module import *
# Aliased imports: import numpy as np
# Conditional imports: if sys.version_info > (3, 8): import new_module
# Dynamic imports: importlib.import_module(variable_name)

# Strategy: Handle common patterns, log complex ones for manual review
```

## Performance Considerations

### 1. Caching Strategy

```python
# Cache import resolution results
# Cache AST parsing results
# Cache dependency analysis for unchanged files
# Use file modification times for cache invalidation
```

### 2. Incremental Analysis

```python
# Only re-analyze files that have changed
# Use dependency graph to determine which files need re-documentation
# Support partial graph rebuilding
```

### 3. Memory Management

```python
# Stream large files rather than loading entirely into memory
# Clear AST objects after analysis
# Use weak references where appropriate
```

## Testing Strategy

### Unit Tests

1. **AST Import Extraction**
   - Test various import statement types
   - Test malformed Python files
   - Test edge cases (empty files, syntax errors)

2. **Import Resolution**
   - Test relative imports at various levels
   - Test package vs module resolution
   - Test namespace packages
   - Test unresolvable imports

3. **Graph Operations**
   - Test cycle detection with various cycle types
   - Test topological sorting
   - Test graph construction with large trees

### Integration Tests

1. **End-to-End Dependency Analysis**
   - Real project structures
   - Various Python project layouts
   - Performance with large codebases

2. **Edge Case Projects**
   - Circular dependency projects
   - Complex relative import structures
   - Mixed package/module structures

### Test Fixtures

```
tests/fixtures/
├── simple_linear/          # A → B → C linear dependencies
├── simple_circular/        # A → B → C → A circular
├── complex_structure/      # Real-world project structure
├── namespace_packages/     # PEP 420 namespace packages
├── relative_imports/       # Complex relative import patterns
└── malformed/             # Syntax errors, missing files
```

## API Reference

### Public Methods

```python
# Core API for integration with documentation system
def analyze_project_dependencies(module_tree_root: ModuleNode,
                                ast_analyzer: Optional[ASTAnalyzer] = None) -> DependencyGraph:
    """
    Main entry point for dependency analysis.

    Args:
        module_tree_root: Root of the module tree to analyze
        ast_analyzer: Optional configured AST analyzer (for dependency injection)

    Returns:
        Configured DependencyGraph with analysis complete
    """
    graph = DependencyGraph(module_tree_root, ast_analyzer)
    graph.build_graph()
    return graph

def generate_dependency_report(dependency_graph: DependencyGraph) -> str:
    """Generate human-readable dependency analysis report."""
```

### Configuration Options

```python
@dataclass
class DependencyAnalysisConfig:
    """Configuration for dependency analysis."""
    ignore_external_imports: bool = True
    ignore_test_files: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: ['test_*', '*_test.py'])
    include_stdlib: bool = False
    max_recursion_depth: int = 50
    enable_caching: bool = True
    cache_dir: Optional[str] = None

    # AST Analyzer configuration
    ast_analyzer_config: Optional['AnalysisConfig'] = None
```

## Success Metrics

1. **Accuracy**: Successfully resolves >95% of internal project imports
2. **Performance**: Analyzes 1000 file project in <30 seconds
3. **Robustness**: Handles malformed files gracefully without crashing
4. **Coverage**: Supports all common Python import patterns
5. **Usability**: Clear error messages and progress reporting

---

*This specification provides the detailed design for the dependency graph system. Implementation should follow this specification while maintaining flexibility for optimization and enhancement.*
