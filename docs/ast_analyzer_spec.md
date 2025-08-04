# AST Analyzer Specification

## Overview

The AST Analyzer is responsible for parsing Python source code and extracting import statements using Python's Abstract Syntax Tree (AST) module. This component provides the foundation for dependency analysis by accurately identifying all import relationships within Python files.

## Core Functionality

### 1. Import Statement Extraction

The AST Analyzer must handle all forms of Python import statements:

```python
# Direct module imports
import os
import sys as system
import numpy, pandas

# From imports
from os import path
from sys import argv as arguments
from collections import defaultdict, Counter

# Relative imports
from . import sibling_module
from .. import parent_module
from ...grandparent import uncle_module

# Star imports
from module import *

# Conditional imports
if sys.version_info >= (3, 8):
    import new_feature
else:
    import old_feature

# Dynamic imports (limited static analysis)
importlib.import_module('dynamic_module')
```

### 2. AST Node Types Handled

```python
ast.Import       # import module_name
ast.ImportFrom   # from module import name
```

### 3. Import Resolution Logic

The analyzer must replicate Python's import resolution mechanism for project-internal files:

1. **Absolute Imports**: Resolve against project root and Python path
2. **Relative Imports**: Resolve relative to current file's package
3. **Package Imports**: Handle `__init__.py` files correctly
4. **Namespace Packages**: Support PEP 420 namespace packages

## Implementation Specification

### 1. ASTAnalyzer Class

```python
import ast
import os
from pathlib import Path
from typing import List, Optional, Dict, Set
from dataclasses import dataclass

class ASTAnalyzer:
    """
    Analyzes Python source code using AST to extract import dependencies.
    """

    def __init__(self, project_root: str, config: Optional[AnalysisConfig] = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or AnalysisConfig()
        self.resolution_cache = {}  # Cache for import resolution
        self.error_log = []

    def analyze_file(self, file_path: str) -> FileAnalysis:
        """
        Analyze a single Python file for import statements and dependencies.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            FileAnalysis object containing all import information
        """

    def extract_imports(self, source_code: str, file_path: str) -> List[ImportStatement]:
        """
        Extract all import statements from Python source code.

        Args:
            source_code: Python source code as string
            file_path: Path to the source file (for relative import resolution)

        Returns:
            List of ImportStatement objects
        """

    def resolve_import(self, import_stmt: ImportStatement,
                      current_file_path: str) -> Optional[ResolvedImport]:
        """
        Resolve an import statement to actual file paths within the project.

        Args:
            import_stmt: The import statement to resolve
            current_file_path: Path of the file containing the import

        Returns:
            ResolvedImport object or None if external/unresolvable
        """
```

### 2. Data Structures

```python
@dataclass
class ImportStatement:
    """Represents a single import statement extracted from AST."""

    # Basic import information
    module_name: str                    # e.g., 'os.path', 'numpy'
    imported_names: List[str]           # e.g., ['join', 'exists'] for 'from os.path import join, exists'
    aliases: Dict[str, str]             # e.g., {'np': 'numpy'} for 'import numpy as np'

    # Import type and location
    is_from_import: bool                # True for 'from x import y', False for 'import x'
    is_relative: bool                   # True for relative imports (from . import x)
    relative_level: int                 # Number of dots in relative import (0 for absolute)

    # Source location information
    line_number: int                    # Line number in source file
    column_offset: int                  # Column offset in source file

    # AST node reference (for debugging)
    ast_node: Optional[ast.AST] = None

@dataclass
class ResolvedImport:
    """Represents a resolved import with actual file paths."""

    import_statement: ImportStatement
    resolved_paths: List[str]           # Actual file paths this import resolves to
    resolution_type: str                # 'file', 'package', 'namespace_package', 'builtin', 'external'
    is_internal: bool                   # True if resolves to project-internal files

@dataclass
class FileAnalysis:
    """Complete analysis results for a single file."""

    file_path: str
    source_lines: int
    imports: List[ImportStatement]
    resolved_imports: List[ResolvedImport]
    internal_dependencies: List[str]    # Paths to internal files this file depends on
    external_imports: List[str]         # External modules imported
    unresolved_imports: List[ImportStatement]  # Imports that couldn't be resolved
    errors: List[str]                   # Any errors encountered during analysis
    analysis_time: float                # Time taken for analysis

@dataclass
class AnalysisConfig:
    """Configuration for AST analysis."""

    # Import filtering
    include_stdlib: bool = False
    include_external: bool = False
    ignore_patterns: List[str] = None   # Patterns to ignore (e.g., ['test_*'])

    # Resolution behavior
    follow_symlinks: bool = True
    case_sensitive: bool = True
    max_recursion_depth: int = 10

    # Performance options
    enable_caching: bool = True
    cache_timeout: int = 3600           # Cache timeout in seconds

    # Standard library detection
    use_stdlib_list: bool = True        # Use stdlib_list package if available
    python_version: Optional[str] = None  # Specific Python version for stdlib detection

    def __post_init__(self):
        if self.ignore_patterns is None:
            self.ignore_patterns = ['test_*', '*_test.py', '__pycache__/*']

        if self.python_version is None:
            import sys
            self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
```

### 3. AST Visitor Implementation

```python
class ImportVisitor(ast.NodeVisitor):
    """
    AST visitor to extract import statements from Python code.

    This class extends ast.NodeVisitor from Python's standard library AST module,
    which provides a visitor pattern for traversing Abstract Syntax Trees.
    The visitor pattern allows us to walk through all nodes in the AST and
    selectively process nodes of interest (import statements in our case).
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = []
        self.errors = []

    def visit_Import(self, node: ast.Import) -> None:
        """Handle 'import module' statements."""
        for alias in node.names:
            import_stmt = ImportStatement(
                module_name=alias.name,
                imported_names=[],
                aliases={alias.asname: alias.name} if alias.asname else {},
                is_from_import=False,
                is_relative=False,
                relative_level=0,
                line_number=node.lineno,
                column_offset=node.col_offset,
                ast_node=node
            )
            self.imports.append(import_stmt)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle 'from module import name' statements."""
        if node.module is None and node.level == 0:
            # Handle malformed imports gracefully
            self.errors.append(f"Malformed import at line {node.lineno}")
            return

        module_name = node.module or ""
        imported_names = []
        aliases = {}

        for alias in node.names:
            imported_names.append(alias.name)
            if alias.asname:
                aliases[alias.asname] = alias.name

        import_stmt = ImportStatement(
            module_name=module_name,
            imported_names=imported_names,
            aliases=aliases,
            is_from_import=True,
            is_relative=node.level > 0,
            relative_level=node.level or 0,
            line_number=node.lineno,
            column_offset=node.col_offset,
            ast_node=node
        )
        self.imports.append(import_stmt)
```

### 4. Import Resolution Algorithm

```python
def resolve_import(self, import_stmt: ImportStatement, current_file_path: str) -> Optional[ResolvedImport]:
    """
    Resolve import statement to actual file paths using Python's import resolution rules.
    """

    # Step 1: Handle relative imports
    if import_stmt.is_relative:
        return self._resolve_relative_import(import_stmt, current_file_path)

    # Step 2: Handle absolute imports
    return self._resolve_absolute_import(import_stmt, current_file_path)

def _resolve_relative_import(self, import_stmt: ImportStatement, current_file_path: str) -> Optional[ResolvedImport]:
    """
    Resolve relative imports like 'from . import module' or 'from ..package import module'.

    Algorithm:
    1. Determine current file's package by walking up directory tree
    2. Apply relative level (number of dots) to find target package
    3. Resolve module name within target package
    4. Return resolved file paths
    """

    current_file = Path(current_file_path).resolve()
    current_package = self._find_package_root(current_file)

    # Calculate target package based on relative level
    target_package = current_package
    for _ in range(import_stmt.relative_level):
        target_package = target_package.parent
        if not self._is_package(target_package):
            return None  # Relative import goes outside package boundaries

    # Resolve module within target package
    if import_stmt.module_name:
        module_path = target_package / import_stmt.module_name.replace('.', os.sep)
    else:
        module_path = target_package

    return self._resolve_module_path(module_path, import_stmt)

def _resolve_absolute_import(self, import_stmt: ImportStatement, current_file_path: str) -> Optional[ResolvedImport]:
    """
    Resolve absolute imports like 'import os' or 'from package.module import function'.

    Algorithm:
    1. Check if import is within project (starts with project package names)
    2. If internal, resolve to project file paths
    3. If external, classify as external/builtin and return None
    """

    module_parts = import_stmt.module_name.split('.')

    # Try to resolve within project structure
    for search_path in self._get_search_paths():
        potential_path = search_path
        for part in module_parts:
            potential_path = potential_path / part

        resolved = self._resolve_module_path(potential_path, import_stmt)
        if resolved:
            return resolved

    # Check if it's a standard library or external module
    if self._is_stdlib_module(import_stmt.module_name):
        return ResolvedImport(
            import_statement=import_stmt,
            resolved_paths=[],
            resolution_type='builtin',
            is_internal=False
        )

    return None  # External module

def _resolve_module_path(self, module_path: Path, import_stmt: ImportStatement) -> Optional[ResolvedImport]:
    """
    Resolve a potential module path to actual file(s).

    Handles:
    - Regular modules (module.py)
    - Packages (__init__.py)
    - Namespace packages (directory without __init__.py)
    """

    resolved_paths = []
    resolution_type = None

    # Check for regular module file
    if module_path.with_suffix('.py').exists():
        resolved_paths.append(str(module_path.with_suffix('.py')))
        resolution_type = 'file'

    # Check for package
    elif module_path.is_dir():
        init_file = module_path / '__init__.py'
        if init_file.exists():
            resolved_paths.append(str(init_file))
            resolution_type = 'package'
        elif self._is_namespace_package(module_path):
            resolved_paths.append(str(module_path))
            resolution_type = 'namespace_package'

    if resolved_paths:
        return ResolvedImport(
            import_statement=import_stmt,
            resolved_paths=resolved_paths,
            resolution_type=resolution_type,
            is_internal=self._is_internal_path(resolved_paths[0])
        )

    return None
```

### 5. Helper Methods

```python
def _find_package_root(self, file_path: Path) -> Path:
    """Find the root package containing the given file."""
    current = file_path.parent
    while current.parent != current:  # Not at filesystem root
        if not (current / '__init__.py').exists():
            return current.parent
        current = current.parent
    return current

def _is_package(self, path: Path) -> bool:
    """Check if path is a Python package."""
    return path.is_dir() and (path / '__init__.py').exists()

def _is_namespace_package(self, path: Path) -> bool:
    """Check if path is a PEP 420 namespace package."""
    return (path.is_dir() and
            not (path / '__init__.py').exists() and
            any(p.suffix == '.py' for p in path.iterdir()))

def _is_internal_path(self, file_path: str) -> bool:
    """Check if file path is within the project."""
    try:
        Path(file_path).resolve().relative_to(self.project_root)
        return True
    except ValueError:
        return False

def _get_search_paths(self) -> List[Path]:
    """Get list of paths to search for modules."""
    return [self.project_root]

def _is_stdlib_module(self, module_name: str) -> bool:
    """
    Check if module is part of Python standard library.

    Uses the stdlib_list package for accurate detection of standard library modules
    across different Python versions. Falls back to a basic check if stdlib_list
    is not available.
    """
    root_module = module_name.split('.')[0]

    try:
        # Use stdlib_list package for accurate detection
        import stdlib_list
        import sys

        # Get standard library modules for current Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        stdlib_modules = stdlib_list.stdlib_list(python_version)

        return root_module in stdlib_modules

    except ImportError:
        # Fallback to basic check if stdlib_list is not available
        # This is a subset of standard library modules - not comprehensive
        basic_stdlib_modules = {
            'os', 'sys', 'ast', 'json', 'csv', 'sqlite3', 'urllib', 'http',
            'collections', 'itertools', 'functools', 'operator', 'pathlib',
            'datetime', 'time', 'calendar', 'locale', 'logging', 're', 'math',
            'random', 'statistics', 'decimal', 'fractions', 'string', 'textwrap',
            'unicodedata', 'io', 'tempfile', 'shutil', 'glob', 'fnmatch',
            'typing', 'dataclasses', 'contextlib', 'abc', 'enum', 'warnings',
            'weakref', 'copy', 'pickle', 'base64', 'hashlib', 'hmac', 'secrets',
            'struct', 'codecs', 'array', 'bisect', 'heapq', 'queue', 'threading',
            'multiprocessing', 'concurrent', 'subprocess', 'signal', 'socket',
            'ssl', 'email', 'mimetypes', 'zipfile', 'tarfile', 'gzip', 'bz2',
            'lzma', 'configparser', 'argparse', 'getopt', 'unittest', 'doctest'
        }

        return root_module in basic_stdlib_modules
```

## Error Handling

### 1. Syntax Errors

```python
def safe_parse_ast(self, source_code: str, file_path: str) -> Optional[ast.AST]:
    """Safely parse source code, handling syntax errors."""
    try:
        return ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        self.error_log.append(f"Syntax error in {file_path}: {e}")
        return None
    except Exception as e:
        self.error_log.append(f"Unexpected error parsing {file_path}: {e}")
        return None
```

### 2. File Access Errors

```python
def safe_read_file(self, file_path: str) -> Optional[str]:
    """Safely read file content, handling encoding and access errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try alternative encodings
        for encoding in ['latin1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        self.error_log.append(f"Could not decode {file_path}")
        return None
    except (IOError, OSError) as e:
        self.error_log.append(f"Could not read {file_path}: {e}")
        return None
```

### 3. Import Resolution Errors

```python
def handle_resolution_error(self, import_stmt: ImportStatement, error: Exception) -> None:
    """Handle errors during import resolution."""
    self.error_log.append(
        f"Failed to resolve import '{import_stmt.module_name}' "
        f"at line {import_stmt.line_number}: {error}"
    )
```

## Testing Strategy

### Unit Tests

```python
# Test cases for import extraction
def test_simple_imports():
    """Test extraction of basic import statements."""

def test_from_imports():
    """Test extraction of from-import statements."""

def test_relative_imports():
    """Test extraction of relative imports at various levels."""

def test_aliased_imports():
    """Test imports with aliases."""

def test_star_imports():
    """Test star imports."""

# Test cases for import resolution
def test_absolute_import_resolution():
    """Test resolution of absolute imports."""

def test_relative_import_resolution():
    """Test resolution of relative imports."""

def test_package_import_resolution():
    """Test resolution of package imports."""

def test_namespace_package_resolution():
    """Test resolution of namespace packages."""

# Test cases for error handling
def test_syntax_error_handling():
    """Test handling of files with syntax errors."""

def test_missing_file_handling():
    """Test handling of missing imported files."""

def test_circular_import_detection():
    """Test detection of circular imports."""
```

### Integration Tests

```python
def test_real_project_analysis():
    """Test analysis of real Python projects."""

def test_large_project_performance():
    """Test performance with large projects."""

def test_complex_import_patterns():
    """Test complex real-world import patterns."""
```

## Dependencies and Installation

### Required Dependencies

```python
# Core dependencies (always required)
ast          # Built-in Python module
os           # Built-in Python module
pathlib      # Built-in Python module
dataclasses  # Built-in Python module (Python 3.7+)
typing       # Built-in Python module

# Recommended dependencies
stdlib_list  # For accurate standard library detection
```

### Installation Considerations

The AST analyzer is designed to work with minimal dependencies. The `stdlib_list` package
is recommended for production use to ensure accurate standard library detection across
different Python versions:

```bash
pip install stdlib-list
```

If `stdlib_list` is not available, the analyzer will fall back to a basic set of
known standard library modules, which may be less accurate for edge cases.

## Performance Optimization

### 1. Caching Strategy

```python
# Cache AST parsing results
# Cache import resolution results
# Use file modification time for cache invalidation
# Serialize cache to disk for persistence
```

### 2. Parallel Processing

```python
# Process multiple files in parallel
# Use multiprocessing for CPU-bound AST parsing
# Coordinate shared cache access safely
```

### 3. Memory Management

```python
# Stream large files instead of loading entirely
# Clear AST references after processing
# Use generators for large result sets
```

## Success Criteria

1. **Accuracy**: Correctly extracts >99% of standard import patterns
2. **Performance**: Analyzes 1000 files in <10 seconds
3. **Robustness**: Handles malformed files without crashing
4. **Coverage**: Supports Python 3.6+ syntax and import patterns
5. **Maintainability**: Clear, well-documented code with comprehensive tests

---

*This specification provides the detailed design for the AST analyzer component. Implementation should prioritize accuracy and robustness while maintaining good performance characteristics.*
