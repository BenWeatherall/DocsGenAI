# Documentation Orchestrator Specification

## Overview

The Documentation Orchestrator is responsible for coordinating the enhanced documentation workflow that uses dependency graph ordering and context passing. It replaces the simple bottom-up approach with a sophisticated dependency-aware system that ensures files are documented in the correct order with appropriate context.

## Core Responsibilities

1. **Dependency-Aware Ordering**: Document files in topological order based on import dependencies
2. **Context Management**: Pass relevant documentation context between dependent files
3. **Progress Tracking**: Monitor documentation progress and handle resumption
4. **Circular Dependency Handling**: Manage documentation of circular dependency groups
5. **Error Recovery**: Gracefully handle errors and allow partial completion

## Architecture

### 1. DocumentationOrchestrator Class

```python
from typing import List, Dict, Optional, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

class DocumentationState(Enum):
    """States for documentation progress tracking."""
    PENDING = "pending"
    ANALYZING_DEPENDENCIES = "analyzing_dependencies"
    READY_FOR_DOCUMENTATION = "ready_for_documentation"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"

class DocumentationOrchestrator:
    """
    Orchestrates the dependency-aware documentation process.
    """

    def __init__(self, module_tree_root: ModuleNode, config: OrchestratorConfig):
        self.root = module_tree_root
        self.config = config
        self.dependency_graph = None
        self.documentation_order = []
        self.progress_tracker = ProgressTracker()
        self.context_manager = ContextManager()
        self.error_handler = ErrorHandler()

    def orchestrate_documentation(self) -> DocumentationResult:
        """
        Main orchestration method that coordinates the entire documentation process.

        Returns:
            DocumentationResult with summary of the process
        """

    def build_dependency_graph(self) -> DependencyGraph:
        """Build the dependency graph for the module tree."""

    def determine_documentation_order(self) -> List[Union[ModuleNode, List[ModuleNode]]]:
        """
        Determine the order in which nodes should be documented.

        Delegates to DependencyGraph.get_documentation_order() which is the
        single source of truth for documentation ordering logic.
        """

    def document_in_order(self, documentation_order: List[Union[ModuleNode, List[ModuleNode]]]) -> None:
        """Document nodes in the specified order, handling context passing."""

    def document_single_node(self, node: ModuleNode) -> bool:
        """Document a single node with appropriate context."""

    def document_cycle_group(self, cycle_nodes: List[ModuleNode]) -> bool:
        """Document a group of nodes with circular dependencies."""

    def generate_final_report(self) -> str:
        """Generate a comprehensive report of the documentation process."""
```

### 2. Supporting Classes

```python
@dataclass
class OrchestratorConfig:
    """Configuration for the documentation orchestrator."""

    # Dependency analysis options
    enable_dependency_analysis: bool = True
    ignore_external_dependencies: bool = True
    ignore_test_files: bool = True

    # Context passing options
    max_context_length: int = 5000  # Maximum characters of context to pass
    context_summary_ratio: float = 0.3  # Ratio of original to summary length
    include_dependency_signatures: bool = True

    # Error handling options
    continue_on_errors: bool = True
    max_retry_attempts: int = 3
    fallback_to_simple_workflow: bool = True

    # Performance options
    parallel_documentation: bool = False
    max_workers: int = 4
    batch_size: int = 10

    # Parallel implementation strategy:
    # When enabled, document independent nodes (nodes with no dependencies
    # or whose dependencies are already completed) in parallel using ThreadPoolExecutor.
    # This requires careful coordination of shared state and progress tracking.

    # Output options
    save_intermediate_results: bool = True
    generate_dependency_report: bool = True
    create_visualization: bool = True

@dataclass
class DocumentationResult:
    """Results of the documentation orchestration process."""

    success: bool
    total_nodes: int
    documented_nodes: int
    skipped_nodes: int
    error_nodes: int
    circular_dependencies: List[List[ModuleNode]]
    processing_time: float
    dependency_graph: Optional[DependencyGraph]
    error_log: List[str]
    warnings: List[str]

class ProgressTracker:
    """Tracks progress of the documentation process."""

    def __init__(self):
        self.node_states = {}  # ModuleNode -> DocumentationState
        self.start_time = None
        self.completion_times = {}  # ModuleNode -> completion_time

    def set_node_state(self, node: ModuleNode, state: DocumentationState) -> None:
        """Update the state of a node."""

    def get_node_state(self, node: ModuleNode) -> DocumentationState:
        """Get the current state of a node."""

    def get_ready_nodes(self) -> List[ModuleNode]:
        """Get nodes that are ready for documentation."""

    def get_completion_percentage(self) -> float:
        """Get overall completion percentage."""

    def generate_progress_report(self) -> str:
        """Generate a human-readable progress report."""

class ContextManager:
    """Manages documentation context passing between nodes."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.documentation_cache = {}  # ModuleNode -> documentation_string
        self.context_cache = {}  # ModuleNode -> context_summary

    def get_context_for_node(self, node: ModuleNode) -> str:
        """Get relevant context for documenting a node."""

    def cache_node_documentation(self, node: ModuleNode, documentation: str) -> None:
        """Cache documentation for a node."""

    def create_context_summary(self, documentation: str) -> str:
        """
        Create a summary of documentation for context passing.

        Summarization Strategy:
        1. Truncation-based: If documentation is under max_context_length, use as-is
        2. Sentence-based: Extract first few sentences up to context_summary_ratio
        3. Paragraph-based: Extract first paragraph if under length limit
        4. Keyword extraction: Extract key function/class definitions and docstrings

        The goal is to preserve the most important information about what the
        module does and exports, while staying within length limits.
        """

        if len(documentation) <= self.config.max_context_length:
            return documentation

        # Strategy 1: Sentence-based summarization
        sentences = self._split_into_sentences(documentation)
        target_length = int(len(documentation) * self.config.context_summary_ratio)

        summary_sentences = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > target_length:
                break
            summary_sentences.append(sentence)
            current_length += len(sentence)

        if summary_sentences:
            summary = ' '.join(summary_sentences)
            if len(summary) <= self.config.max_context_length:
                return summary

        # Strategy 2: Paragraph-based (first paragraph)
        first_paragraph = documentation.split('\n\n')[0]
        if len(first_paragraph) <= self.config.max_context_length:
            return first_paragraph

        # Strategy 3: Hard truncation with ellipsis
        return documentation[:self.config.max_context_length - 3] + "..."

    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting for context summarization."""
        import re
        # Simple sentence boundary detection
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def get_dependency_context(self, node: ModuleNode) -> Dict[str, str]:
        """Get context from all dependencies of a node."""

        context = {}

        for dependency in node.dependencies:
            if dependency in self.documentation_cache:
                doc = self.documentation_cache[dependency]
                summary = self.create_context_summary(doc)
                context[dependency.name] = summary

        return context
```

## Orchestration Algorithm

### 1. Main Orchestration Flow

```python
def orchestrate_documentation(self) -> DocumentationResult:
    """
    Main orchestration algorithm:

    1. Build dependency graph
    2. Detect circular dependencies
    3. Determine documentation order
    4. Initialize progress tracking
    5. Document nodes in order with context passing
    6. Handle errors and retries
    7. Generate final report
    """

    result = DocumentationResult()
    result.start_time = time.time()

    try:
        # Phase 1: Dependency Analysis
        self.progress_tracker.set_overall_phase("analyzing_dependencies")
        self.dependency_graph = self.build_dependency_graph()
        result.dependency_graph = self.dependency_graph

        # Phase 2: Order Determination
        self.progress_tracker.set_overall_phase("determining_order")
        self.documentation_order = self.determine_documentation_order()

        # Phase 3: Documentation Generation
        self.progress_tracker.set_overall_phase("documenting")
        self.document_in_order(self.documentation_order)

        # Phase 4: Final Processing
        self.progress_tracker.set_overall_phase("finalizing")
        result.success = self._finalize_documentation()

    except Exception as e:
        if self.config.fallback_to_simple_workflow:
            logging.warning(f"Dependency-aware workflow failed: {e}. Falling back to simple workflow.")
            result = self._fallback_to_simple_workflow()
        else:
            result.success = False
            result.error_log.append(f"Orchestration failed: {e}")

    result.processing_time = time.time() - result.start_time
    return result
```

### 2. Dependency-Aware Documentation Order

```python
def determine_documentation_order(self) -> List[Union[ModuleNode, List[ModuleNode]]]:
    """
    Determine documentation order by delegating to DependencyGraph.

    The DependencyGraph class is the single source of truth for documentation
    ordering logic. This method simply delegates to it and handles any
    orchestrator-specific concerns.
    """

    # Delegate to DependencyGraph for ordering logic
    documentation_order = self.dependency_graph.get_documentation_order()

    # Log the determined order for debugging
    self._log_documentation_order(documentation_order)

    return documentation_order

def _log_documentation_order(self, order: List[Union[ModuleNode, List[ModuleNode]]]) -> None:
    """Log the determined documentation order for debugging purposes."""

    logging.info("Documentation order determined:")
    for i, item in enumerate(order):
        if isinstance(item, list):
            # Circular dependency group
            cycle_names = [node.name for node in item]
            logging.info(f"  {i+1}. Cycle: {' -> '.join(cycle_names)} -> {cycle_names[0]}")
        else:
            # Single node
            logging.info(f"  {i+1}. {item.name}")
```

### 3. Context-Aware Documentation

```python
def document_single_node(self, node: ModuleNode) -> bool:
    """
    Document a single node with context from its dependencies.

    Algorithm:
    1. Check if all dependencies are documented
    2. Gather context from dependencies
    3. Generate documentation with context
    4. Cache documentation for future dependents
    5. Update progress tracking
    """

    # Check if node is ready
    if not self._is_node_ready_for_documentation(node):
        return False

    # Set state to documenting
    self.progress_tracker.set_node_state(node, DocumentationState.DOCUMENTING)

    try:
        # Gather context from dependencies
        dependency_context = self.context_manager.get_dependency_context(node)

        # Generate documentation with context
        documentation = self._generate_documentation_with_context(node, dependency_context)

        # Cache documentation
        self.context_manager.cache_node_documentation(node, documentation)

        # Save to file
        save_documentation_to_file(node, documentation)

        # Update state
        self.progress_tracker.set_node_state(node, DocumentationState.COMPLETED)
        return True

    except Exception as e:
        self.progress_tracker.set_node_state(node, DocumentationState.ERROR)
        self.error_handler.log_error(node, e)
        return False

def _generate_documentation_with_context(self, node: ModuleNode, dependency_context: Dict[str, str]) -> str:
    """Generate documentation for a node with dependency context."""

    # Build enhanced prompt with dependency context
    prompt_parts = []

    if node.is_package:
        prompt_parts.extend(self._build_package_prompt(node))
    else:
        prompt_parts.extend(self._build_module_prompt(node))

    # Add dependency context
    if dependency_context:
        prompt_parts.append("\n## Context from Dependencies:")
        prompt_parts.append("The following modules are imported by this file. Use their documentation to understand the context and avoid redundant explanations:")

        for dep_name, dep_doc in dependency_context.items():
            prompt_parts.append(f"\n### {dep_name}")
            prompt_parts.append(dep_doc)

    # Add specific instructions for context usage
    prompt_parts.append(
        "\n## Documentation Instructions:"
        "1. Reference the imported modules' purposes without repeating their full documentation"
        "2. Focus on how this module uses its dependencies rather than redescribing them"
        "3. Explain the unique value this module adds beyond its dependencies"
        "4. Keep explanations concise while maintaining clarity"
    )

    full_prompt = "\n".join(prompt_parts)
    return get_llm_documentation(full_prompt)
```

### 4. Circular Dependency Handling

```python
def document_cycle_group(self, cycle_nodes: List[ModuleNode]) -> bool:
    """
    Document a group of nodes with circular dependencies as a unit.

    Strategy:
    1. Analyze the cycle to understand the relationships
    2. Generate documentation that explains the cycle
    3. Document each node with awareness of the circular relationship
    4. Provide clear explanation of the interdependencies
    """

    # Mark all nodes in cycle as documenting
    for node in cycle_nodes:
        self.progress_tracker.set_node_state(node, DocumentationState.DOCUMENTING)

    try:
        # Analyze cycle relationships
        cycle_analysis = self._analyze_cycle_relationships(cycle_nodes)

        # Generate cycle overview documentation
        cycle_overview = self._generate_cycle_overview(cycle_nodes, cycle_analysis)

        # Document each node with cycle context
        for node in cycle_nodes:
            node_documentation = self._generate_cycle_node_documentation(
                node, cycle_nodes, cycle_overview, cycle_analysis
            )

            # Cache and save documentation
            self.context_manager.cache_node_documentation(node, node_documentation)
            save_documentation_to_file(node, node_documentation)

            # Update state
            self.progress_tracker.set_node_state(node, DocumentationState.COMPLETED)

        return True

    except Exception as e:
        # Mark all nodes as error
        for node in cycle_nodes:
            self.progress_tracker.set_node_state(node, DocumentationState.ERROR)
            self.error_handler.log_error(node, e)
        return False

def _analyze_cycle_relationships(self, cycle_nodes: List[ModuleNode]) -> Dict:
    """Analyze the relationships within a circular dependency group."""

    relationships = {}

    for node in cycle_nodes:
        relationships[node] = {
            'imports_from_cycle': [],
            'imported_by_cycle': [],
            'import_statements': []
        }

        # Find imports within the cycle
        for dependency in node.dependencies:
            if dependency in cycle_nodes:
                relationships[node]['imports_from_cycle'].append(dependency)

        for dependent in node.dependents:
            if dependent in cycle_nodes:
                relationships[node]['imported_by_cycle'].append(dependent)

    return relationships

def _generate_cycle_overview(self, cycle_nodes: List[ModuleNode], cycle_analysis: Dict) -> str:
    """Generate an overview explanation of the circular dependency."""

    prompt_parts = [
        f"Generate a brief overview of a circular dependency between {len(cycle_nodes)} Python modules:",
        f"Modules involved: {', '.join(node.name for node in cycle_nodes)}",
        "",
        "The circular dependency structure is as follows:"
    ]

    for node, analysis in cycle_analysis.items():
        imports = [dep.name for dep in analysis['imports_from_cycle']]
        if imports:
            prompt_parts.append(f"- {node.name} imports: {', '.join(imports)}")

    prompt_parts.extend([
        "",
        "Please provide:",
        "1. A brief explanation of why this circular dependency exists",
        "2. The likely architectural pattern or design choice that creates this cycle",
        "3. The collective purpose these modules serve together",
        "",
        "Keep this overview concise (2-3 sentences) as it will be included in each module's documentation."
    ])

    return get_llm_documentation("\n".join(prompt_parts))
```

### 5. Error Handling and Recovery

```python
class ErrorHandler:
    """Handles errors during the documentation process."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.error_log = []
        self.retry_counts = {}

    def log_error(self, node: ModuleNode, error: Exception) -> None:
        """Log an error for a specific node."""
        error_entry = {
            'node': node.name,
            'path': node.path,
            'error': str(error),
            'timestamp': time.time(),
            'retry_count': self.retry_counts.get(node, 0)
        }
        self.error_log.append(error_entry)

    def should_retry(self, node: ModuleNode) -> bool:
        """Determine if a node should be retried after error."""
        retry_count = self.retry_counts.get(node, 0)
        return retry_count < self.config.max_retry_attempts

    def mark_retry(self, node: ModuleNode) -> None:
        """Mark a node for retry."""
        self.retry_counts[node] = self.retry_counts.get(node, 0) + 1

    def generate_error_report(self) -> str:
        """Generate a comprehensive error report."""
        if not self.error_log:
            return "No errors encountered during documentation process."

        report_parts = [
            f"Documentation Errors ({len(self.error_log)} total):",
            ""
        ]

        for error in self.error_log:
            report_parts.append(
                f"- {error['node']} ({error['path']}): {error['error']}"
            )
            if error['retry_count'] > 0:
                report_parts.append(f"  (Attempted {error['retry_count']} retries)")

        return "\n".join(report_parts)
```

## Integration with Existing System

### 1. ModuleNode Enhancements

```python
# Additional fields for ModuleNode class
class ModuleNode:
    # Existing fields...

    # Dependency tracking
    dependencies: List['ModuleNode'] = field(default_factory=list)
    dependents: List['ModuleNode'] = field(default_factory=list)
    import_statements: List[ImportStatement] = field(default_factory=list)

    # Documentation state
    documentation_state: DocumentationState = DocumentationState.PENDING
    documentation_context: Dict[str, str] = field(default_factory=dict)

    # Cycle handling
    cycle_group: Optional[List['ModuleNode']] = None
    cycle_id: Optional[str] = None

    def is_ready_for_documentation(self) -> bool:
        """Check if this node is ready for documentation."""
        # All dependencies must be completed
        for dep in self.dependencies:
            if dep.documentation_state != DocumentationState.COMPLETED:
                return False
        return True

    def get_dependency_documentation_context(self) -> Dict[str, str]:
        """Get documentation context from dependencies."""
        context = {}
        for dep in self.dependencies:
            if dep.documentation and dep.documentation_state == DocumentationState.COMPLETED:
                # Use summary or full documentation based on length
                context[dep.name] = self._create_context_summary(dep.documentation)
        return context
```

### 2. Enhanced Main Function

```python
def main():
    """Enhanced main function with dependency-aware orchestration."""

    # Get repository path
    repo_path = input("Please enter the absolute path to the Python repository you want to document: ")

    if not os.path.isdir(repo_path):
        print(f"Error: The provided path '{repo_path}' is not a valid directory.")
        return

    # Build module tree (existing functionality)
    print(f"\nBuilding module tree for repository: {repo_path}")
    module_tree_root = build_module_tree(repo_path)

    if not module_tree_root:
        print("Failed to build the module tree. Exiting.")
        return

    # Read project files (existing functionality)
    print("Reading project configuration files...")
    project_files = read_project_files(repo_path)

    # Create orchestrator configuration
    config = OrchestratorConfig()

    # Option to enable/disable dependency analysis
    use_dependency_analysis = input("\nUse dependency-aware documentation? (y/n, default: y): ").lower() != 'n'
    config.enable_dependency_analysis = use_dependency_analysis

    if use_dependency_analysis:
        print("\nStarting dependency-aware documentation process...")
        orchestrator = DocumentationOrchestrator(module_tree_root, config)
        result = orchestrator.orchestrate_documentation()

        # Print results
        print(f"\n--- Documentation Complete ---")
        print(f"Success: {result.success}")
        print(f"Documented: {result.documented_nodes}/{result.total_nodes} nodes")

        if result.circular_dependencies:
            print(f"Circular dependencies found: {len(result.circular_dependencies)} groups")

        if result.error_log:
            print(f"Errors encountered: {len(result.error_log)}")

        # Generate comprehensive report
        if config.generate_dependency_report:
            report = orchestrator.generate_final_report()
            with open(os.path.join(repo_path, "DEPENDENCY_ANALYSIS_REPORT.md"), 'w') as f:
                f.write(report)
            print("Dependency analysis report saved to DEPENDENCY_ANALYSIS_REPORT.md")

    else:
        print("\nUsing simple documentation workflow...")
        # Fall back to existing workflow
        if module_tree_root.is_package or module_tree_root.children:
            document_module_tree_bottom_up(module_tree_root, project_files)
        else:
            print("No Python modules or packages found in the specified directory.")
            return

    print("\nScript execution finished.")
```

## Testing Strategy

### Unit Tests

```python
def test_dependency_order_calculation():
    """Test calculation of documentation order."""

def test_context_generation():
    """Test generation of context from dependencies."""

def test_cycle_detection_and_handling():
    """Test detection and handling of circular dependencies."""

def test_error_recovery():
    """Test error handling and retry mechanisms."""

def test_progress_tracking():
    """Test progress tracking functionality."""
```

### Integration Tests

```python
def test_end_to_end_orchestration():
    """Test complete orchestration process."""

def test_fallback_to_simple_workflow():
    """Test fallback when dependency analysis fails."""

def test_large_project_orchestration():
    """Test orchestration with large projects."""
```

## Performance Considerations

### 1. Memory Management
- Clear documentation cache for nodes no longer needed
- Use streaming for large dependency contexts
- Implement configurable cache size limits

### 2. Parallel Processing
- Document independent nodes in parallel
- Use async/await for I/O bound operations
- Coordinate access to shared state safely

### 3. Optimization Strategies
- Cache dependency analysis results
- Implement incremental documentation updates
- Use lazy evaluation for context generation

## Success Criteria

1. **Correctness**: Documents files in correct dependency order 100% of the time
2. **Context Quality**: Passes relevant context without excessive verbosity
3. **Error Handling**: Gracefully handles errors and provides useful diagnostics
4. **Performance**: Processes large projects efficiently with minimal overhead
5. **Usability**: Clear progress reporting and intuitive configuration options

---

*This specification defines the enhanced documentation workflow that leverages dependency analysis for improved context and ordering. The implementation should maintain backward compatibility while providing significant improvements in documentation quality.*
