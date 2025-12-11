"""
Import analysis module.

This module provides functionality to analyze import statements and determine
whether they are external or internal to the project.
"""

from pathlib import Path

from .core_types import ImportStatement, ModuleNode
from .import_extractor import ImportExtractor


class ImportAnalyzer:
    """
    Analyzes import statements and determines their classification.

    This class provides methods to analyze import statements, determine
    whether they are external or internal to the project, and resolve
    relative imports.
    """

    def __init__(self, project_root: str) -> None:
        """
        Initialize the import analyzer.

        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root).resolve()
        self.module_cache: dict[str, list[ImportStatement]] = {}
        self.external_modules: set[str] = set()
        self.extractor = ImportExtractor()

    def extract_imports_from_file(self, file_path: str) -> list[ImportStatement]:
        """
        Extract import statements from a Python file.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            list of ImportStatement objects found in the file

        Raises:
            SyntaxError: If the file contains invalid Python syntax
            OSError: If the file cannot be read
        """
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                source_code = f.read()
            return self.extractor.extract_imports(source_code)
        except FileNotFoundError:
            raise OSError(f"File not found: {file_path}")
        except UnicodeDecodeError:
            raise OSError(f"Cannot decode file: {file_path}")

    def extract_imports_from_module(
        self, module_node: ModuleNode
    ) -> list[ImportStatement]:
        """
        Extract import statements from a module node.

        Args:
            module_node: ModuleNode object containing the module to analyze

        Returns:
            list of ImportStatement objects found in the module
        """
        if not module_node.content:
            return []

        return self.extractor.extract_imports(module_node.content)

    def resolve_relative_import(
        self, import_stmt: ImportStatement, current_file_path: str
    ) -> str | None:
        """
        Resolve a relative import to an absolute path.

        Args:
            import_stmt: The ImportStatement to resolve
            current_file_path: Path to the file containing the import

        Returns:
            Resolved absolute path, or None if resolution fails
        """
        if not import_stmt.is_relative:
            return None

        current_path = Path(current_file_path).resolve()
        current_dir = current_path.parent

        # Navigate up the directory structure based on relative level
        target_dir = current_dir
        for _ in range(import_stmt.relative_level - 1):
            target_dir = target_dir.parent

        # Handle the case where we're importing from the current directory level
        if import_stmt.relative_level == 1:
            target_dir = current_dir
        elif import_stmt.relative_level > 1:
            # Navigate up (relative_level - 1) directories
            target_dir = current_dir
            for _ in range(import_stmt.relative_level - 1):
                target_dir = target_dir.parent

        # If no module name specified (e.g., 'from . import x'),
        # we need to look for the imported item in the target directory
        if not import_stmt.module_name:
            # This is a complex case - for now, we'll skip it
            return None

        # Construct the target module path
        if import_stmt.module_name:
            module_parts = import_stmt.module_name.split(".")
            for part in module_parts:
                target_dir = target_dir / part

        # Look for the module file
        possible_files = [
            target_dir / "__init__.py",
            target_dir.with_suffix(".py"),
            target_dir / f"{target_dir.name}.py",
        ]

        for file_path in possible_files:
            if file_path.exists():
                return str(file_path)

        return None

    def is_external_import(self, import_stmt: ImportStatement) -> bool:
        """
        Determine if an import statement refers to an external module.

        Args:
            import_stmt: The ImportStatement to analyze

        Returns:
            True if the import is external, False otherwise
        """
        if import_stmt.is_relative:
            return False

        module_name = import_stmt.module_name
        if not module_name:
            return False

        # Check if it's a standard library module
        if self._is_standard_library_module(module_name):
            return True

        # Simplified check: only return True if we're certain it's external
        # Unknown modules default to internal (non-external)
        # Check if it's a project module - if so, it's not external
        if self._is_project_module(module_name):
            return False

        # For unknown modules, default to internal (non-external)
        # This is a simplified check that treats unknown modules as project modules
        return False

    def _is_standard_library_module(self, module_name: str) -> bool:
        """
        Check if a module name refers to a standard library module.

        Args:
            module_name: Name of the module to check

        Returns:
            True if it's a standard library module, False otherwise
        """
        # Common standard library modules
        stdlib_modules = {
            "os",
            "sys",
            "pathlib",
            "typing",
            "collections",
            "datetime",
            "json",
            "re",
            "logging",
            "argparse",
            "subprocess",
            "shutil",
            "tempfile",
            "urllib",
            "http",
            "socket",
            "threading",
            "multiprocessing",
            "asyncio",
            "contextlib",
            "functools",
            "itertools",
            "operator",
            "abc",
            "enum",
            "dataclasses",
            "typing_extensions",
            "pydantic",
            "numpy",
            "pandas",
            "matplotlib",
            "requests",
            "flask",
            "django",
            "sqlalchemy",
            "pytest",
            "unittest",
            "mock",
            "pytest_mock",
        }

        # Check exact match
        if module_name in stdlib_modules:
            return True

        # Check if it's a submodule of a standard library module
        base_module = module_name.split(".")[0]
        return base_module in stdlib_modules

    def _is_project_module(self, module_name: str) -> bool:
        """
        Check if a module name refers to a project module.

        Args:
            module_name: Name of the module to check

        Returns:
            True if it's a project module, False otherwise
        """
        # Check if the module exists in the project structure
        module_path = self.project_root / f"{module_name}.py"
        if module_path.exists():
            return True

        # Check for package directories
        package_path = self.project_root / module_name / "__init__.py"

        return package_path.exists()

    def analyze_project_imports(
        self, module_nodes: list[ModuleNode]
    ) -> dict[str, list[ImportStatement]]:
        """
        Analyze imports for all modules in the project.

        Args:
            module_nodes: list of ModuleNode objects to analyze

        Returns:
            Dictionary mapping module paths to their import statements
        """
        project_imports = {}

        for module_node in module_nodes:
            # Read from file if content is not available
            if module_node.content:
                imports = self.extract_imports_from_module(module_node)
            else:
                imports = self.extract_imports_from_file(module_node.path)
            project_imports[str(module_node.path)] = imports

            # Track external modules
            for import_stmt in imports:
                if self.is_external_import(import_stmt):
                    self.external_modules.add(import_stmt.module_name)

        return project_imports

    def get_external_dependencies(self) -> set[str]:
        """
        Get the set of external dependencies found in the project.

        Returns:
            set of external module names
        """
        return self.external_modules.copy()

    def clear_cache(self) -> None:
        """Clear the module cache."""
        self.module_cache.clear()
        self.external_modules.clear()

    def get_import_statistics(
        self, project_imports: dict[str, list[ImportStatement]]
    ) -> dict[str, int]:
        """
        Get statistics about imports in the project.

        Args:
            project_imports: Dictionary mapping module paths to import statements

        Returns:
            Dictionary containing import statistics
        """
        total_imports = 0
        external_imports = 0
        internal_imports = 0
        relative_imports = 0

        for imports in project_imports.values():
            for import_stmt in imports:
                total_imports += 1
                if import_stmt.is_relative:
                    relative_imports += 1
                elif self.is_external_import(import_stmt):
                    external_imports += 1
                else:
                    internal_imports += 1

        return {
            "total_imports": total_imports,
            "external_imports": external_imports,
            "internal_imports": internal_imports,
            "relative_imports": relative_imports,
        }
