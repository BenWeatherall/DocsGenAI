# GenAI Docs

Generate comprehensive documentation for Python projects using AI. This tool analyzes your codebase hierarchically, starting from the lowest-level modules and working upwards to create complete documentation.

## Executive Summary

GenAI Docs uses Google's Gemini 2.0 Flash model to automatically generate documentation for Python projects. It employs a bottom-up approach that minimizes context window usage by:

1. **Hierarchical Analysis**: Scans your project structure to identify modules and packages
2. **Bottom-Up Processing**: Documents leaf modules first, then uses their documentation to inform parent module documentation
3. **Context Optimization**: Each documentation call uses only relevant information, preventing hallucinations
4. **Comprehensive Coverage**: Generates purpose, interface, usage examples, and relationships between modules
5. **File-Based Output**: Saves documentation as `DOCUMENTATION.md` files in each module's directory
6. **Project-Level Context**: Uses project configuration files (pyproject.toml, README.md, etc.) for root-level documentation

## Installation

```bash
# Install from PyPI
pip install genai-docs

# Or install from source
git clone https://github.com/benweatherall/genai-docs
cd genai-docs
pip install -e .
```

## Usage

### Prerequisites

You'll need a Google AI API key. Set it as an environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

### Basic Usage

```bash
# Run the interactive tool
genai-docs

# Or run directly with Python
python -m genai_docs.main
```

When prompted, enter the absolute path to your Python project. The tool will:

1. Scan your project structure
2. Build a hierarchical tree of modules and packages
3. Read project configuration files (pyproject.toml, README.md, etc.)
4. Generate documentation starting from leaf modules
5. Work upwards to parent modules using child documentation
6. Save `DOCUMENTATION.md` files in each module's directory
7. Display the complete documentation hierarchy

### Output Files

The tool creates `DOCUMENTATION.md` files in each module's directory:

```
my_project/
├── DOCUMENTATION.md          # Project-level documentation
├── pyproject.toml
├── README.md
├── my_package/
│   ├── DOCUMENTATION.md      # Package documentation
│   ├── __init__.py
│   ├── utils/
│   │   ├── DOCUMENTATION.md  # Module documentation
│   │   └── helpers.py
│   └── models/
│       ├── DOCUMENTATION.md  # Module documentation
│       └── data.py
└── main.py
```

### Example Output

```
Documenting: utils (Path: /path/to/project/utils)
Documenting: models (Path: /path/to/project/models)
Documenting: my_package (Path: /path/to/project/my_package)
Documenting: genai-docs (Project Root)

--- Documentation Complete ---
Generated Documentation Summary:

- genai-docs (Project):
  Purpose: A comprehensive data processing framework that provides utilities for...
  Public Interface: The main entry point is the `process_data()` function...
  Installation & Usage: pip install genai-docs...

  - my_package (Package):
    Purpose: Data models for representing structured information...
    Interface: Exports ModelBase class and various data models...

  - utils (Module):
    Purpose: Utility functions for data validation and transformation...
    Interface: Provides validate_input() and transform_data() functions...
```

## Development

### Setup

```bash
# Clone and install in development mode
git clone https://github.com/benweatherall/genai-docs
cd genai-docs
pip install -e ".[dev]"
```

### Code Quality

```bash
# Lint and format code
ruff check genai_docs/
ruff format genai_docs/

# Type checking
mypy genai_docs/

# Run tests
pytest
```

### Project Structure

```
genai-docs/
├── genai_docs/
│   └── main.py          # Main application logic
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

### Key Components

- **ModuleNode**: Represents Python modules/packages in the tree structure
- **build_module_tree()**: Scans directory structure and builds hierarchical tree
- **document_module_tree_bottom_up()**: Recursively documents from leaves to root
- **document_project_root()**: Generates project-level documentation using config files
- **save_documentation_to_file()**: Saves documentation as markdown files
- **get_llm_documentation()**: Interfaces with Gemini 2.0 Flash for documentation generation

The tool automatically handles Python packages (directories with `__init__.py`) and modules (`.py` files), skipping common non-source directories like `__pycache__`, `.git`, etc.

### Context Optimization

This tool is designed to reduce context window usage for AI agents by:

1. **Replacing Code Parsing**: Instead of parsing individual module code, AI agents can reference the generated `DOCUMENTATION.md` files
2. **Rolling Up Context**: Parent modules include child documentation summaries, reducing the need to examine individual sub-modules
3. **Project-Level Focus**: Root documentation focuses on public interfaces and user-facing functionality
4. **File-Based References**: Each module's documentation is self-contained in its directory

This approach allows AI agents to work with smaller, more focused context windows while maintaining comprehensive understanding of the codebase structure and functionality.
