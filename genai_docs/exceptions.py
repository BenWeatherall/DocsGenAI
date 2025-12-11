"""
Custom exceptions for GenAI Docs.

This module defines the exception hierarchy used throughout the application.
"""


class GenAIDocsError(Exception):
    """Base exception for all GenAI Docs errors."""


class ConfigurationError(GenAIDocsError):
    """Raised when there is a configuration error."""


class LLMError(GenAIDocsError):
    """Raised when there is an error with the LLM API."""


class DocumentationError(GenAIDocsError):
    """Raised when there is an error during documentation generation."""


class FileManagerError(GenAIDocsError):
    """Raised when there is an error with file operations."""


class DependencyGraphError(GenAIDocsError):
    """Raised when there is an error building or analyzing the dependency graph."""
