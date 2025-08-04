"""
GenAI Docs - AI-powered Python project documentation generator.

This package provides tools to automatically generate comprehensive documentation
for Python projects using AI, with dependency analysis and hierarchical documentation.
"""

from .ast_analyzer import ASTAnalyzer
from .core_types import DependencyGraph, ImportStatement, ModuleNode
from .dependency_graph import DependencyAnalyzer, DependencyGraphBuilder
from .main import main

__version__ = "0.1.0"
__author__ = "Ben Weatherall"

__all__ = [
    "ASTAnalyzer",
    "DependencyAnalyzer",
    "DependencyGraph",
    "DependencyGraphBuilder",
    "ImportStatement",
    "ModuleNode",
    "main",
]
