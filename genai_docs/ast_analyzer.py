"""
AST analyzer module.

This module provides the main ASTAnalyzer class and re-exports
the import extraction and analysis components for convenience.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core_types import ImportStatement, ModuleNode
from .import_analyzer import ImportAnalyzer
from .import_extractor import ImportExtractor


class ASTAnalyzer:
    """
    Analyzes Python source code using AST to extract various code elements.

    This class provides comprehensive AST analysis including function extraction,
    class extraction, import analysis, and code complexity metrics.
    """

    def __init__(self, project_root: str):
        """
        Initialize the AST analyzer.

        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root).resolve()
        self.import_analyzer = ImportAnalyzer(str(project_root))
        self.extractor = ImportExtractor()

    def parse_python_code(self, code: str) -> Optional[ast.Module]:
        """
        Parse Python code into an AST.

        Args:
            code: Python source code as string

        Returns:
            AST Module node or None if parsing fails
        """
        if not code.strip():
            return None

        try:
            return ast.parse(code)
        except (SyntaxError, IndentationError):
            return None

    def extract_functions(self, code: str) -> List[Any]:
        """
        Extract function definitions from Python code.

        Args:
            code: Python source code as string

        Returns:
            List of function objects with name attribute
        """
        tree = self.parse_python_code(code)
        if not tree:
            return []

        functions = []
        # Only look at top-level functions (not inside classes)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Create a simple object with name attribute for test compatibility
                class FunctionInfo:
                    def __init__(self, name, line_number, args, docstring, is_async):
                        self.name = name
                        self.line_number = line_number
                        self.args = args
                        self.docstring = docstring
                        self.is_async = is_async

                func_info = FunctionInfo(
                    name=node.name,
                    line_number=node.lineno,
                    args=[arg.arg for arg in node.args.args],
                    docstring=ast.get_docstring(node),
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                )
                functions.append(func_info)

        return functions

    def extract_classes(self, code: str) -> List[Any]:
        """
        Extract class definitions from Python code.

        Args:
            code: Python source code as string

        Returns:
            List of class objects with name attribute
        """
        tree = self.parse_python_code(code)
        if not tree:
            return []

        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Create a simple object with name attribute for test compatibility
                class ClassInfo:
                    def __init__(self, name, line_number, bases, docstring, methods):
                        self.name = name
                        self.line_number = line_number
                        self.bases = bases
                        self.docstring = docstring
                        self.methods = methods

                # Extract methods
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(
                            {
                                "name": item.name,
                                "line_number": item.lineno,
                                "args": [arg.arg for arg in item.args.args],
                                "docstring": ast.get_docstring(item),
                                "is_async": isinstance(item, ast.AsyncFunctionDef),
                            }
                        )

                class_info = ClassInfo(
                    name=node.name,
                    line_number=node.lineno,
                    bases=[
                        base.id for base in node.bases if isinstance(base, ast.Name)
                    ],
                    docstring=ast.get_docstring(node),
                    methods=methods,
                )
                classes.append(class_info)

        return classes

    def extract_imports(self, code: str) -> List[str]:
        """
        Extract import statements from Python code.

        Args:
            code: Python source code as string

        Returns:
            List of import statement strings
        """
        import_statements = self.extractor.extract_imports(code)
        return [str(imp) for imp in import_statements]

    def analyze_module(self, code: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a Python module.

        Args:
            code: Python source code as string

        Returns:
            Dictionary containing analysis results
        """
        tree = self.parse_python_code(code)
        if not tree:
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "docstrings": [],
                "complexity": 0,
            }

        functions = self.extract_functions(code)
        classes = self.extract_classes(code)
        imports = self.extract_imports(code)
        docstrings = self.extract_docstrings(code)
        complexity = self.analyze_complexity(code)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "docstrings": docstrings,
            "complexity": complexity,
        }

    def extract_docstrings(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract docstrings from Python code.

        Args:
            code: Python source code as string

        Returns:
            List of docstring information dictionaries
        """
        tree = self.parse_python_code(code)
        if not tree:
            return []

        docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    doc_info = {
                        "content": docstring,
                        "line_number": node.lineno,
                        "type": type(node).__name__,
                    }
                    if hasattr(node, "name"):
                        doc_info["name"] = node.name
                    docstrings.append(doc_info)

        return docstrings

    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """
        Analyze code complexity using cyclomatic complexity.

        Args:
            code: Python source code as string

        Returns:
            Dictionary containing complexity analysis
        """
        tree = self.parse_python_code(code)
        if not tree:
            return {"functions": []}

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1  # Base complexity

                # Calculate complexity for this function
                for child in ast.walk(node):
                    if isinstance(
                        child, (ast.If, ast.While, ast.For, ast.AsyncFor)
                    ) or isinstance(child, ast.ExceptHandler):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1

                functions.append({"name": node.name, "complexity": complexity})

        return {"functions": functions}

    def extract_type_hints(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract type hints from Python code.

        Args:
            code: Python source code as string

        Returns:
            List of type hint information dictionaries
        """
        tree = self.parse_python_code(code)
        if not tree:
            return []

        type_hints = []
        for node in ast.walk(tree):
            if isinstance(node, ast.arg) and node.annotation:
                hint_info = {
                    "arg_name": node.arg,
                    "annotation": ast.unparse(node.annotation)
                    if hasattr(ast, "unparse")
                    else str(node.annotation),
                    "line_number": node.lineno,
                }
                type_hints.append(hint_info)
            elif isinstance(node, ast.FunctionDef) and node.returns:
                hint_info = {
                    "function": node.name,
                    "return_annotation": ast.unparse(node.returns)
                    if hasattr(ast, "unparse")
                    else str(node.returns),
                    "line_number": node.lineno,
                }
                type_hints.append(hint_info)
            elif isinstance(node, ast.ClassDef):
                # Add class type hints
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and item.annotation:
                        hint_info = {
                            "class": node.name,
                            "attribute": item.target.id
                            if hasattr(item.target, "id")
                            else str(item.target),
                            "annotation": ast.unparse(item.annotation)
                            if hasattr(ast, "unparse")
                            else str(item.annotation),
                            "line_number": item.lineno,
                        }
                        type_hints.append(hint_info)

                # Also add method type hints
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.returns:
                            hint_info = {
                                "class": node.name,
                                "function": item.name,
                                "return_annotation": ast.unparse(item.returns)
                                if hasattr(ast, "unparse")
                                else str(item.returns),
                                "line_number": item.lineno,
                            }
                            type_hints.append(hint_info)

        return type_hints

    def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """
        Analyze dependencies in Python code.

        Args:
            code: Python source code as string

        Returns:
            Dictionary mapping module names to function lists
        """
        import_statements = self.extractor.extract_imports(code)

        dependencies = {}

        # Extract function names from the code
        tree = self.parse_python_code(code)
        function_names = []
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_names.append(node.name)

        # Map imports to functions
        for imp in import_statements:
            module_name = imp.module_name
            if module_name not in dependencies:
                dependencies[module_name] = function_names

        return dependencies

    def is_external_import(self, import_stmt) -> bool:
        """
        Check if an import statement is external to the project.

        Args:
            import_stmt: ImportStatement object

        Returns:
            True if external, False if internal
        """
        return self.import_analyzer.is_external_import(import_stmt)

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
        return self.import_analyzer.analyze_project_imports(module_nodes)


# For backward compatibility, also export ImportAnalyzer
__all__ = ["ASTAnalyzer", "ImportAnalyzer", "ImportExtractor"]
