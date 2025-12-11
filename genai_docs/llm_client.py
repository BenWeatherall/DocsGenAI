"""
LLM client for AI-powered documentation generation.

This module handles all interactions with the Google Generative AI API
for generating documentation content.
"""

import logging
import time
from pathlib import Path

import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader

from .config import config
from .exceptions import LLMError

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
_template_dir = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(_template_dir))


class LLMClient:
    """Client for interacting with the Google Generative AI API."""

    def __init__(self) -> None:
        """Initialize the LLM client."""
        self.model: genai.GenerativeModel | None = None
        self._configure_api()

    def _configure_api(self) -> None:
        """Configure the Google Generative AI API."""
        try:
            genai.configure(api_key=config.api_key)
            self.model = genai.GenerativeModel(config.model_name)
            logger.info(f"Configured LLM client with model: {config.model_name}")
        except Exception as e:
            logger.error(f"Failed to configure LLM client: {e}")
            raise

    def generate_documentation(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate documentation using the LLM with retry logic.

        Args:
            prompt: The text prompt to send to the LLM
            max_retries: Maximum number of retry attempts

        Returns:
            Generated documentation text

        Raises:
            LLMError: If the LLM call fails after retries
        """
        if not self.model:
            raise LLMError("LLM client not properly configured")

        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Sending prompt to LLM (attempt {attempt + 1}/{max_retries})"
                )
                response = self.model.generate_content(
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )

                if (
                    response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                ):
                    result = response.candidates[0].content.parts[0].text
                    logger.debug("Successfully generated documentation")
                    return result

                error_msg = "LLM response structure unexpected or empty"
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                    continue
                raise LLMError(error_msg)

            except Exception as e:
                last_exception = e
                error_msg = f"Failed to generate documentation: {e}"
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = (2**attempt) + (time.time() % 1)
                    time.sleep(wait_time)
                    continue
                raise LLMError(error_msg) from e

        # Should not reach here, but just in case
        raise LLMError(
            "Failed to generate documentation after retries"
        ) from last_exception

    def generate_project_documentation(
        self, project_files: dict[str, str], children_docs: list[str]
    ) -> str:
        """
        Generate documentation for the root project.

        Args:
            project_files: Dictionary containing project file contents
            children_docs: List of child module documentation

        Returns:
            Generated project documentation
        """
        template = _jinja_env.get_template("project_documentation.j2")
        full_prompt = template.render(
            project_files=project_files or {}, children_docs=children_docs or []
        )
        return self.generate_documentation(full_prompt)

    def generate_package_documentation(
        self,
        package_name: str,
        children_docs: list[str],
        init_content: str | None = None,
        dependency_context: str | None = None,
    ) -> str:
        """
        Generate documentation for a Python package.

        Args:
            package_name: Name of the package
            children_docs: List of child module documentation
            init_content: Content of __init__.py file
            dependency_context: Optional context about dependencies

        Returns:
            Generated package documentation
        """
        template = _jinja_env.get_template("package_documentation.j2")
        full_prompt = template.render(
            package_name=package_name,
            children_docs=children_docs or [],
            init_content=init_content,
            dependency_context=dependency_context,
        )
        return self.generate_documentation(full_prompt)

    def generate_module_documentation(
        self,
        module_name: str,
        module_content: str | None = None,
        dependency_context: str | None = None,
    ) -> str:
        """
        Generate documentation for a Python module.

        Args:
            module_name: Name of the module
            module_content: Content of the module file
            dependency_context: Optional context about dependencies

        Returns:
            Generated module documentation
        """
        template = _jinja_env.get_template("module_documentation.j2")
        full_prompt = template.render(
            module_name=module_name,
            module_content=module_content,
            dependency_context=dependency_context,
        )
        return self.generate_documentation(full_prompt)
