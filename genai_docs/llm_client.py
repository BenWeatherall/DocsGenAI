"""
LLM client for AI-powered documentation generation.

This module handles all interactions with the Google Generative AI API
for generating documentation content.
"""

import logging
from typing import Optional

import google.generativeai as genai

from .config import config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with the Google Generative AI API."""

    def __init__(self):
        """Initialize the LLM client."""
        self.model = None
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

    def generate_documentation(self, prompt: str) -> str:
        """
        Generate documentation using the LLM.

        Args:
            prompt: The text prompt to send to the LLM

        Returns:
            Generated documentation text

        Raises:
            RuntimeError: If the LLM call fails
        """
        if not self.model:
            raise RuntimeError("LLM client not properly configured")

        try:
            logger.debug("Sending prompt to LLM")
            response = self.model.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )

            if (response.candidates and
                response.candidates[0].content and
                response.candidates[0].content.parts):
                result = response.candidates[0].content.parts[0].text
                logger.debug("Successfully generated documentation")
                return result
            error_msg = "LLM response structure unexpected or empty"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        except Exception as e:
            error_msg = f"Failed to generate documentation: {e}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    def generate_project_documentation(self, project_files: dict[str, str],
                                     children_docs: list[str]) -> str:
        """
        Generate documentation for the root project.

        Args:
            project_files: Dictionary containing project file contents
            children_docs: List of child module documentation

        Returns:
            Generated project documentation
        """
        prompt_parts = []
        prompt_parts.append(
            "Please provide clear, concise, and comprehensive documentation for this Python project."
        )
        prompt_parts.append("Your documentation should cover:")
        prompt_parts.append(
            "1. **Purpose:** What is the overall goal or functionality of this project/library?"
        )
        prompt_parts.append(
            "2. **Public Interface:** What are the main public classes, functions, or modules that users should interact with?"
        )
        prompt_parts.append(
            "3. **Installation & Usage:** How should users install and use this project?"
        )
        prompt_parts.append(
            "4. **Project Structure:** Provide an overview of the main modules and their purposes."
        )
        prompt_parts.append(
            "5. **Dependencies:** What are the key dependencies and requirements?"
        )

        # Include project configuration files
        if project_files:
            prompt_parts.append("\n## Project Configuration Files:")
            for filename, content in project_files.items():
                prompt_parts.append(f"\n### {filename}")
                prompt_parts.append(f"```\n{content}\n```")

        # Include documentation of children
        if children_docs:
            prompt_parts.append("\n## Sub-modules and Packages:\n")
            for doc in children_docs:
                prompt_parts.append(doc)
        else:
            prompt_parts.append(
                "\nThis project does not contain any sub-modules or packages."
            )

        prompt_parts.append(
            "\n\nFocus on the public-facing interface and user-facing functionality. "
            "Only reference publicly exposed classes, functions, and modules that are "
            "intended for external use. Private implementation details should be omitted."
        )

        full_prompt = "\n".join(prompt_parts)
        return self.generate_documentation(full_prompt)

    def generate_package_documentation(self, package_name: str,
                                     children_docs: list[str],
                                     init_content: Optional[str] = None) -> str:
        """
        Generate documentation for a Python package.

        Args:
            package_name: Name of the package
            children_docs: List of child module documentation
            init_content: Content of __init__.py file

        Returns:
            Generated package documentation
        """
        prompt_parts = []
        prompt_parts.append(
            f"Please provide clear, concise, and comprehensive documentation for the Python package '{package_name}'."
        )
        prompt_parts.append("Your documentation should cover:")
        prompt_parts.append(
            "1. **Purpose:** What is the overall goal or functionality of this package?"
        )
        prompt_parts.append(
            "2. **Interface:** What are the main classes, functions, or variables exposed by this package for external use?"
        )
        prompt_parts.append(
            "3. **Usage:** Provide clear examples of how this package would typically be imported and used."
        )
        prompt_parts.append(
            "4. **Relationship to Sub-modules:** Explain how the sub-modules contribute to the package's overall functionality."
        )

        # Include documentation of children
        if children_docs:
            prompt_parts.append(
                "\nConsider the following as documentation for its direct sub-modules/sub-packages:"
            )
            for doc in children_docs:
                prompt_parts.append(doc)
        else:
            prompt_parts.append(
                "\nThis package does not contain any direct sub-modules or sub-packages."
            )

        # Include content of __init__.py if it exists
        if init_content:
            prompt_parts.append(
                f"\nHere is the content of the package's __init__.py file:\n```python\n{init_content}\n```\n"
            )

        full_prompt = "\n".join(prompt_parts)
        return self.generate_documentation(full_prompt)

    def generate_module_documentation(self, module_name: str,
                                    module_content: Optional[str] = None) -> str:
        """
        Generate documentation for a Python module.

        Args:
            module_name: Name of the module
            module_content: Content of the module file

        Returns:
            Generated module documentation
        """
        prompt_parts = []
        prompt_parts.append(
            f"Please provide clear, concise, and comprehensive documentation for the Python module '{module_name}'."
        )
        prompt_parts.append("Your documentation should cover:")
        prompt_parts.append(
            "1. **Purpose:** What is the specific goal or functionality of this module?"
        )
        prompt_parts.append(
            "2. **Interface:** What are the main functions, classes, or variables exposed by this module for external use?"
        )
        prompt_parts.append(
            "3. **Usage:** Provide clear examples of how this module would typically be imported and used."
        )

        if module_content:
            prompt_parts.append(
                f"\nHere is the Python code for the module:\n```python\n{module_content}\n```\n"
            )
        else:
            prompt_parts.append(
                "\nThis module file is empty or its content could not be read.\n"
            )

        full_prompt = "\n".join(prompt_parts)
        return self.generate_documentation(full_prompt)


# Global LLM client instance
llm_client = LLMClient()
