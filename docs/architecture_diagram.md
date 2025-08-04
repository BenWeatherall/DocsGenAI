# System Architecture Diagram

## Overview

This document provides comprehensive visual representations of the GenAI Docs system architecture, illustrating the flow of data from AST analysis through dependency graph construction to documentation generation and visualization.

The system follows a layered architecture pattern where each layer has distinct responsibilities and clear interfaces. Data flows from bottom to top, with the core analysis layer being the foundation upon which the orchestration and output layers operate.

## High-Level System Architecture

The following diagram shows the overall system architecture with all major components and their relationships:

<function_calls>
<invoke name="create_diagram">
<parameter name="content">graph TB
    subgraph "Input Layer"
        A[Python Project Files] --> B[Module Tree Builder]
        C[Project Config Files] --> B
    end

    subgraph "Core Analysis Layer"
        B --> D[core_types.py<br/>ModuleNode Tree]
        D --> E[ast_analyzer.py<br/>Import Analysis]
        E --> F[dependency_graph.py<br/>Graph Construction]
    end

    subgraph "Orchestration Layer"
        F --> G[doc_orchestrator.py<br/>Documentation Workflow]
        G --> H[ContextManager<br/>Context Passing]
        G --> I[ProgressTracker<br/>State Management]
    end

    subgraph "Output Layer"
        G --> J[LLM Provider<br/>Documentation Generation]
        J --> K[Documentation Files]
        F --> L[visualization.py<br/>Graph Analysis]
        L --> M[Static Images]
        L --> N[Interactive HTML]
        L --> O[Analysis Reports]
    end

    subgraph "External Dependencies"
        P[Python AST Module]
        Q[NetworkX Library]
        R[Graphviz System]
        S[stdlib_list Package]
        T[vis-network CDN]
    end

    E -.-> P
    F -.-> Q
    L -.-> R
    E -.-> S
    L -.-> T

    classDef coreComponent fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef externalDep fill:#fff3e0,stroke:#ef6c00,stroke-width:1px
    classDef outputFile fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class D,E,F,G,H,I coreComponent
    class P,Q,R,S,T externalDep
    class K,M,N,O outputFile

### Architecture Layers

1. **Input Layer**: Handles project file discovery and configuration
2. **Core Analysis Layer**: Performs dependency analysis and graph construction
3. **Orchestration Layer**: Manages the documentation workflow and context passing
4. **Output Layer**: Generates documentation and visualizations

## Core Data Flow

The central data structure is the ModuleNode, which flows through the system and gets enhanced at each stage:

### ModuleNode Enhancement Flow

<function_calls>
<invoke name="create_diagram">
<parameter name="content">stateDiagram-v2
    [*] --> BasicModuleNode: Module Tree Building
    BasicModuleNode --> ModuleNodeWithImports: AST Analysis
    ModuleNodeWithImports --> ModuleNodeWithDeps: Dependency Resolution
    ModuleNodeWithDeps --> ModuleNodeWithOrder: Graph Construction
    ModuleNodeWithOrder --> ModuleNodeWithContext: Context Management
    ModuleNodeWithContext --> ModuleNodeWithDocs: Documentation Generation
    ModuleNodeWithDocs --> [*]: Output Generation

    state BasicModuleNode {
        path
        name
        is_package
        children
    }

    state ModuleNodeWithImports {
        path
        name
        is_package
        children
        --
        import_statements
        resolved_imports
    }

    state ModuleNodeWithDeps {
        path
        name
        is_package
        children
        import_statements
        resolved_imports
        --
        dependencies
        dependents
        cycle_group
    }

    state ModuleNodeWithOrder {
        path
        name
        is_package
        children
        import_statements
        resolved_imports
        dependencies
        dependents
        cycle_group
        --
        documentation_order
    }

    state ModuleNodeWithContext {
        path
        name
        is_package
        children
        import_statements
        resolved_imports
        dependencies
        dependents
        cycle_group
        documentation_order
        --
        dependency_context
        documentation_state
    }

    state ModuleNodeWithDocs {
        path
        name
        is_package
        children
        import_statements
        resolved_imports
        dependencies
        dependents
        cycle_group
        documentation_order
        dependency_context
        documentation_state
        --
        documentation
        visualizations
    }

## Dependency Analysis Workflow

The dependency analysis follows a specific workflow to ensure accurate results:

### AST Analysis and Import Resolution Process

This diagram shows how the system processes Python source files to extract and resolve import statements:

## Documentation Orchestration Flow

The orchestrator manages the complex workflow of dependency-aware documentation:

This diagram illustrates the complete orchestration process, including error handling and retry logic.

## Component Interaction Patterns

### Dependency Injection Pattern

The system uses dependency injection to enable testing and configuration:

- `DependencyGraph` receives an optional `ASTAnalyzer` instance
- `DocumentationOrchestrator` receives configuration objects
- `VisualizationSystem` receives configuration for different output types

### Observer Pattern

Progress tracking uses an observer-like pattern:

- `ProgressTracker` monitors state changes across nodes
- Event callbacks notify about completion and errors
- State transitions are logged for debugging

### Strategy Pattern

Multiple strategies are used throughout the system:

- **Context Summarization**: Different strategies based on content length
- **Import Resolution**: Different approaches for absolute vs relative imports
- **Visualization**: Multiple renderers for different output formats
- **Error Handling**: Different recovery strategies based on error type

## Key Design Decisions

### 1. ModuleNode as Central Data Structure

The `ModuleNode` serves as the central data structure that flows through all system components. This design:

- **Simplifies data flow**: Single object carries all relevant information
- **Enables incremental enhancement**: Each stage adds more data
- **Supports debugging**: Complete history of transformations
- **Facilitates testing**: Easy to create mock objects

### 2. Layered Architecture

The layered approach provides:

- **Clear separation of concerns**: Each layer has distinct responsibilities
- **Testability**: Layers can be tested in isolation
- **Maintainability**: Changes in one layer don't affect others
- **Extensibility**: New layers or components can be added easily

### 3. Graph-First Approach

Using NetworkX as the foundation provides:

- **Proven algorithms**: Topological sorting, cycle detection
- **Performance**: Optimized graph operations
- **Flexibility**: Easy to add new graph-based features
- **Visualization**: Built-in support for graph visualization

### 4. Context-Aware Documentation

The context passing mechanism:

- **Improves quality**: LLM receives relevant dependency information
- **Reduces redundancy**: Avoids repeating explanations
- **Maintains coherence**: Documentation references are consistent
- **Scales efficiently**: Context is summarized for large projects

## Error Handling Strategy

The system implements comprehensive error handling at multiple levels:

### 1. Input Validation
- File existence and readability checks
- Python syntax validation
- Configuration parameter validation

### 2. Analysis Errors
- Graceful handling of unparseable files
- Fallback for unresolvable imports
- Recovery from circular dependency detection

### 3. Generation Errors
- LLM provider failures and retries
- Disk space and permission issues
- Network connectivity problems

### 4. Output Errors
- Visualization rendering failures
- File writing permissions
- Missing external dependencies

## Performance Considerations

### 1. Caching Strategy
- AST parsing results cached by file modification time
- Import resolution cached for identical patterns
- Documentation cached to avoid regeneration

### 2. Parallel Processing
- Independent nodes can be documented in parallel
- AST analysis can use multiprocessing for large projects
- Visualization generation can be parallelized

### 3. Memory Management
- Large files streamed rather than loaded entirely
- AST objects cleared after analysis
- Context summaries limit memory usage

---

*This architecture diagram provides a comprehensive visual and textual overview of the GenAI Docs system design, illustrating how the dependency graph enhancement integrates with the existing architecture while maintaining clarity and maintainability.*
