"""
Import extraction module.

This module provides functionality to extract import statements from Python code
using the Abstract Syntax Tree (AST) parser.
"""

import ast
from typing import List

from .core_types import ImportStatement


class ImportExtractor(ast.NodeVisitor):
    """
    AST visitor that extracts import statements from Python code.

    This class traverses the AST of a Python module and identifies all
    import and from-import statements, converting them to ImportStatement objects.
    """

    def __init__(self):
        """Initialize the import extractor."""
        self.imports: List[ImportStatement] = []
        self.current_line = 0

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements (e.g., 'import os', 'import os as operating_system')."""
        for alias in node.names:
            import_stmt = ImportStatement(
                module_name=alias.name,
                alias=alias.asname,
                from_import=False,
                line_number=node.lineno,
                is_relative=False,
                relative_level=0
            )
            self.imports.append(import_stmt)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements (e.g., 'from os import path', 'from . import x')."""
        # Handle relative imports
        is_relative = node.level > 0
        module_name = node.module if node.module else ""

        # For relative imports, we need to handle the case where module is None
        # (e.g., 'from . import x' where node.module is None)
        if is_relative and not module_name:
            module_name = ""

        for alias in node.names:
            import_stmt = ImportStatement(
                module_name=module_name,
                alias=alias.asname,
                from_import=True,
                imported_items=[alias.name],
                line_number=node.lineno,
                is_relative=is_relative,
                relative_level=node.level
            )
            self.imports.append(import_stmt)

        self.generic_visit(node)

    def extract_imports(self, source_code: str) -> List[ImportStatement]:
        """
        Extract import statements from Python source code.

        Args:
            source_code: Python source code as a string

        Returns:
            List of ImportStatement objects found in the code

        Raises:
            SyntaxError: If the code contains invalid Python syntax
        """
        try:
            tree = ast.parse(source_code)
            self.imports = []
            self.visit(tree)
            return self.imports
        except SyntaxError as e:
            raise SyntaxError(f"Invalid Python syntax: {e}") from e
