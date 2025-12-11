"""
Command-line interface for GenAI Docs.

This module provides a clean CLI interface for the documentation generator,
handling command-line arguments and user interaction.
"""

import argparse
import logging
import sys
from pathlib import Path

from .cache import DocumentationCache
from .config import config
from .core_types import ModuleNode
from .documentation_generator import DocumentationGenerator
from .exceptions import GenAIDocsError
from .file_manager import file_manager
from .llm_client import LLMClient
from .tree_builder import tree_builder
from .version import __version__

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive documentation for Python projects using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  genai-docs /path/to/project
  genai-docs /path/to/project --output /path/to/docs
  genai-docs /path/to/project --verbose
  genai-docs /path/to/project --dry-run
        """,
    )

    parser.add_argument("project_path", help="Path to the Python project to document")

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for documentation (default: same as project)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be documented without generating files",
    )

    parser.add_argument("--model", help="LLM model to use (default: gemini-2.0-flash)")

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of all documentation, ignoring cache",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of generated documentation",
    )

    parser.add_argument(
        "--no-dependency-graph",
        action="store_true",
        help="Disable dependency-aware ordering (use simple tree traversal)",
    )

    parser.add_argument(
        "--version", action="version", version=f"genai-docs {__version__}"
    )

    return parser


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def validate_project_path(project_path: str) -> bool:
    """
    Validate that the provided project path is valid.

    Args:
        project_path: Path to validate

    Returns:
        True if path is valid, False otherwise
    """
    path = Path(project_path)
    if not path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        return False
    if not path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        return False
    return True


def build_and_validate_tree(project_path: str) -> ModuleNode:
    """
    Build the module tree and validate it.

    Args:
        project_path: Path to the project root

    Returns:
        Root node of the module tree

    Raises:
        ValueError: If tree building fails
    """
    logger.info(f"Building module tree for: {project_path}")
    module_tree_root = tree_builder.build_module_tree(project_path)

    if not module_tree_root:
        raise ValueError("Failed to build module tree")

    if not module_tree_root.children and not module_tree_root.is_package:
        raise ValueError(
            "No Python modules or packages found in the specified directory"
        )

    logger.info("Module tree built successfully")
    return module_tree_root


def generate_documentation(
    module_tree_root: ModuleNode,
    project_path: str,
    doc_generator: DocumentationGenerator,
    dry_run: bool = False,
) -> None:
    """
    Generate documentation for the entire module tree.

    Args:
        module_tree_root: Root node of the module tree
        project_path: Path to the project root
        doc_generator: Documentation generator instance
        dry_run: If True, don't actually generate documentation
    """
    if dry_run:
        logger.info("DRY RUN: Would read project configuration files...")
        logger.info("DRY RUN: Would start documentation generation...")
        return

    logger.info("Reading project configuration files...")
    project_files = file_manager.read_project_files(project_path)

    logger.info("Starting documentation generation (bottom-up approach)...")
    doc_generator.document_module_tree_bottom_up(module_tree_root, project_files)

    logger.info("Documentation generation completed")


def print_summary(
    module_tree_root: ModuleNode,
    doc_generator: DocumentationGenerator,
    dry_run: bool = False,
) -> None:
    """
    Print a summary of the generated documentation.

    Args:
        module_tree_root: Root node of the module tree
        doc_generator: Documentation generator instance
        dry_run: If True, indicate this is a dry run
    """
    if dry_run:
        print("\n--- DRY RUN: Documentation Summary ---")
        print("The following would be documented:")
    else:
        print("\n--- Documentation Complete ---")
        print("Generated Documentation Summary:")

    print(doc_generator.get_documentation_summary(module_tree_root))


def validate_results(
    module_tree_root: ModuleNode,
    doc_generator: DocumentationGenerator,
    dry_run: bool = False,
) -> None:
    """
    Validate the generated documentation and print results.

    Args:
        module_tree_root: Root node of the module tree
        doc_generator: Documentation generator instance
        dry_run: If True, don't validate actual results
    """
    if dry_run:
        print("\n--- DRY RUN: Would validate results ---")
        return

    validation = doc_generator.validate_documentation(module_tree_root)

    print("\n--- Validation Results ---")
    print(f"Total nodes: {validation['stats']['total_nodes']}")
    print(f"Successfully documented: {validation['stats']['documented_nodes']}")
    print(f"Failed: {validation['stats']['failed_nodes']}")
    print(f"Empty documentation: {validation['stats']['empty_documentation']}")

    if validation["issues"]:
        print("\nIssues found:")
        for issue in validation["issues"]:
            print(f"  - {issue}")

    if validation["warnings"]:
        print("\nWarnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

    if validation["valid"]:
        print("\n✅ Documentation generation completed successfully!")
    else:
        print("\n❌ Documentation generation completed with issues")


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Setup configuration
        config.load_from_environment()

        # Override model if specified
        if args.model:
            config.model_name = args.model

        # Set configuration flags
        config.force_regenerate = args.force
        config.use_cache = not args.no_cache
        config.use_dependency_graph = not args.no_dependency_graph
        config.verbose = args.verbose

        config.validate()

        # Setup logging
        setup_logging(verbose=args.verbose)

        # Validate project path
        if not validate_project_path(args.project_path):
            return 1

        # Set project configuration
        config.set_project_root(args.project_path)

        # Set output directory if specified
        if args.output:
            config.set_output_dir(args.output)

        # Create LLM client and documentation generator
        llm_client = LLMClient()
        doc_generator = DocumentationGenerator(llm_client=llm_client)

        # Initialize cache if enabled
        if config.use_cache and not args.dry_run:
            cache = DocumentationCache()
            cache.initialize(config.project_root)
            doc_generator.cache = cache
            doc_generator.force_regenerate = config.force_regenerate
            doc_generator.use_dependency_graph = config.use_dependency_graph

        # Build and validate module tree
        module_tree_root = build_and_validate_tree(args.project_path)

        # Generate documentation
        generate_documentation(
            module_tree_root, args.project_path, doc_generator, args.dry_run
        )

        # Print summary
        print_summary(module_tree_root, doc_generator, args.dry_run)

        # Validate results
        validate_results(module_tree_root, doc_generator, args.dry_run)

        return 0

    except KeyboardInterrupt:
        logger.info("Documentation generation interrupted by user")
        return 1
    except GenAIDocsError as e:
        logger.error(f"Documentation generation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
