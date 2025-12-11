"""
Main entry point for GenAI Docs.

This module provides a simple interactive interface that delegates to the CLI.
For programmatic usage, use the CLI module directly.
"""

import sys

from .cli import main as cli_main


def main() -> int:
    """
    Main function that provides an interactive interface.

    This function prompts the user for a project path and then delegates
    to the CLI with appropriate arguments.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("GenAI Docs - Interactive Mode")
    print("=" * 50)
    repo_path = input(
        "\nPlease enter the absolute path to the Python repository you want to document: "
    ).strip()

    if not repo_path:
        print("Error: No path provided")
        return 1

    # Delegate to CLI with the provided path
    # Simulate command-line arguments
    import sys

    original_argv = sys.argv
    sys.argv = ["genai-docs", repo_path]
    try:
        return cli_main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    sys.exit(main())
