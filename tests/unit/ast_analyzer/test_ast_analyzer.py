"""
Unit tests for the AST analyzer module.

This module tests the AST analysis functionality including
code parsing, function extraction, and dependency analysis.
"""

import ast

from genai_docs.ast_analyzer import ASTAnalyzer


class TestASTAnalyzer:
    """Test the ASTAnalyzer class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = ASTAnalyzer("/tmp")

    def test_parse_python_code_success(self):
        """Test successful parsing of Python code."""
        code = "def test_function():\n    return True"
        result = self.analyzer.parse_python_code(code)

        assert result is not None
        assert isinstance(result, ast.Module)

    def test_parse_python_code_syntax_error(self):
        """Test parsing with syntax error."""
        code = "def test_function():\n    return"  # This is actually valid Python
        result = self.analyzer.parse_python_code(code)

        assert result is not None  # This should parse successfully

        # Test with actual syntax error
        invalid_code = "def test_function():\n    return +"  # Invalid syntax
        result = self.analyzer.parse_python_code(invalid_code)

        assert result is None

    def test_extract_functions_simple(self):
        """Test extracting functions from simple code."""
        code = """
def function1():
    pass

def function2():
    return True
"""
        functions = self.analyzer.extract_functions(code)

        assert len(functions) == 2
        assert any(f.name == "function1" for f in functions)
        assert any(f.name == "function2" for f in functions)

    def test_extract_classes_simple(self):
        """Test extracting classes from simple code."""
        code = """
class Class1:
    pass

class Class2:
    def method(self):
        pass
"""
        classes = self.analyzer.extract_classes(code)

        assert len(classes) == 2
        assert any(c.name == "Class1" for c in classes)
        assert any(c.name == "Class2" for c in classes)

    def test_extract_imports_simple(self):
        """Test extracting imports from simple code."""
        code = """
import os
from pathlib import Path
from typing import List, Dict
"""
        imports = self.analyzer.extract_imports(code)

        assert len(imports) >= 3
        assert any("os" in imp for imp in imports)
        assert any("pathlib" in imp for imp in imports)
        assert any("typing" in imp for imp in imports)

    def test_analyze_module_comprehensive(self):
        """Test comprehensive module analysis."""
        code = """
import os
from pathlib import Path

def helper_function():
    return "helper"

class TestClass:
    def __init__(self):
        self.value = 42

    def method(self):
        return self.value

def main_function():
    instance = TestClass()
    return instance.method()
"""
        analysis = self.analyzer.analyze_module(code)

        assert "functions" in analysis
        assert "classes" in analysis
        assert "imports" in analysis

        assert len(analysis["functions"]) == 2
        assert len(analysis["classes"]) == 1
        assert len(analysis["imports"]) >= 2

    def test_extract_docstrings(self):
        """Test extracting docstrings from code."""
        code = '''
def documented_function():
    """This is a docstring."""
    pass

class DocumentedClass:
    """Class docstring."""

    def method(self):
        """Method docstring."""
        pass
'''
        docstrings = self.analyzer.extract_docstrings(code)

        assert len(docstrings) >= 3
        assert any("This is a docstring" in doc['content'] for doc in docstrings)
        assert any("Class docstring" in doc['content'] for doc in docstrings)
        assert any("Method docstring" in doc['content'] for doc in docstrings)

    def test_analyze_complexity(self):
        """Test complexity analysis."""
        code = """
def simple_function():
    return True

def complex_function():
    result = 0
    for i in range(10):
        if i % 2 == 0:
            for j in range(i):
                result += j
    return result
"""
        complexity = self.analyzer.analyze_complexity(code)

        assert "functions" in complexity
        assert len(complexity["functions"]) == 2

        # Simple function should have lower complexity
        simple_func = next(f for f in complexity["functions"] if f["name"] == "simple_function")
        complex_func = next(f for f in complexity["functions"] if f["name"] == "complex_function")

        assert simple_func["complexity"] < complex_func["complexity"]

    def test_extract_type_hints(self):
        """Test extracting type hints from code."""
        code = """
from typing import List, Dict, Optional

def typed_function(param: str, items: List[int]) -> Optional[Dict[str, int]]:
    return {"count": len(items)}

class TypedClass:
    def __init__(self, value: int):
        self.value: int = value

    def get_value(self) -> int:
        return self.value
"""
        type_hints = self.analyzer.extract_type_hints(code)

        assert len(type_hints) >= 3
        assert any("typed_function" in hint["function"] for hint in type_hints)
        assert any("TypedClass" in hint["class"] for hint in type_hints if "class" in hint)

    def test_analyze_dependencies(self):
        """Test dependency analysis."""
        code = """
import os
from pathlib import Path
from typing import List

def function_using_os():
    return os.getcwd()

def function_using_pathlib():
    return Path.cwd()

def function_using_typing():
    items: List[str] = []
    return items
"""
        dependencies = self.analyzer.analyze_dependencies(code)

        assert "os" in dependencies
        assert "pathlib" in dependencies
        assert "typing" in dependencies

        # Check that functions are associated with their dependencies
        os_functions = dependencies["os"]
        pathlib_functions = dependencies["pathlib"]

        assert "function_using_os" in os_functions
        assert "function_using_pathlib" in pathlib_functions

    def test_handle_empty_code(self):
        """Test handling of empty code."""
        empty_code = ""
        analysis = self.analyzer.analyze_module(empty_code)

        assert analysis["functions"] == []
        assert analysis["classes"] == []
        assert analysis["imports"] == []

    def test_handle_comments_only(self):
        """Test handling of code with only comments."""
        comment_code = "# This is a comment\n# Another comment"
        analysis = self.analyzer.analyze_module(comment_code)

        assert analysis["functions"] == []
        assert analysis["classes"] == []
        assert analysis["imports"] == []

    def test_extract_async_functions(self):
        """Test extracting async functions."""
        code = """
async def async_function():
    await some_operation()
    return "result"

def sync_function():
    return "sync"
"""
        functions = self.analyzer.extract_functions(code)

        assert len(functions) == 2
        async_func = next(f for f in functions if f.name == "async_function")
        sync_func = next(f for f in functions if f.name == "sync_function")

        assert async_func.is_async
        assert not sync_func.is_async
