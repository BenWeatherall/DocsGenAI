# GenAI Docs User Guide

## Introduction

GenAI Docs is an AI-powered documentation generator for Python projects that analyzes code dependencies and generates comprehensive documentation with proper context awareness. This guide covers installation, configuration, and usage of the enhanced dependency-aware system.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Advanced Usage](#advanced-usage)
5. [Understanding Output](#understanding-output)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Installation

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for large projects)
- Internet connection for LLM API calls
- Optional: Graphviz for static visualizations

### Basic Installation

```bash
# Install the basic package
pip install genai-docs

# Or from source
git clone https://github.com/your-org/genai-docs.git
cd genai-docs
pip install -e .
```

### Optional Dependencies

For enhanced functionality, install optional dependencies:

```bash
# For accurate standard library detection
pip install stdlib-list

# For static graph visualizations (requires system Graphviz)
pip install graphviz

# Install system Graphviz
# On Ubuntu/Debian:
sudo apt install graphviz

# On macOS:
brew install graphviz

# On Windows:
# Download from https://graphviz.org/download/
```

### Verification

Verify your installation:

```bash
python -c "import genai_docs; print('GenAI Docs installed successfully')"
```

## Quick Start

### Basic Usage

1. **Navigate to your Python project**:
   ```bash
   cd /path/to/your/python/project
   ```

2. **Run GenAI Docs**:
   ```bash
   python -m genai_docs
   ```

3. **Follow the prompts**:
   - Enter the absolute path to your Python repository
   - Choose whether to use dependency-aware documentation (recommended: yes)
   - Choose whether to generate visualizations (recommended: yes)

### Example Session

```bash
$ python -m genai_docs

Please enter the absolute path to the Python repository you want to document:
/home/user/my-python-project

Building module tree for repository: /home/user/my-python-project
✓ Found 15 Python modules
✓ Built module tree successfully

Use dependency-aware documentation? (y/n, default: y): y

Analyzing dependencies...
✓ Extracted 47 import statements
✓ Resolved 42 internal dependencies
✓ Detected 1 circular dependency group
✓ Generated documentation order

Generate dependency visualizations? (y/n, default: y): y

Starting dependency-aware documentation process...
[1/15] Documenting utils.py (no dependencies)
[2/15] Documenting config.py (no dependencies)
[3/15] Documenting models.py (depends on: utils)
[4/15] Documenting circular group: views.py, controllers.py
[5/15] Documenting main.py (depends on: config, models, views)
...

--- Documentation Complete ---
Success: True
Documented: 15/15 nodes
Circular dependencies found: 1 groups
Processing time: 2.3 minutes

✓ Documentation files saved to project directory
✓ Dependency analysis report saved to DEPENDENCY_ANALYSIS_REPORT.md
✓ Visualizations saved to dependency_analysis/

Script execution finished.
```

## Configuration

### Command Line Options

```bash
# Basic usage
python -m genai_docs

# Specify project path directly
python -m genai_docs --project /path/to/project

# Disable dependency analysis (use simple workflow)
python -m genai_docs --no-dependencies

# Disable visualizations
python -m genai_docs --no-visualizations

# Enable verbose logging
python -m genai_docs --verbose

# Use specific configuration file
python -m genai_docs --config my_config.json
```

### Configuration File

Create a `genai_docs_config.json` file in your project root:

```json
{
  "orchestrator": {
    "enable_dependency_analysis": true,
    "continue_on_errors": true,
    "max_retry_attempts": 3,
    "fallback_to_simple_workflow": true,
    "max_context_length": 5000,
    "context_summary_ratio": 0.3,
    "parallel_documentation": false,
    "generate_dependency_report": true,
    "create_visualization": true
  },
  "dependency_analysis": {
    "ignore_external_imports": true,
    "ignore_test_files": true,
    "ignore_patterns": ["test_*", "*_test.py", "__pycache__/*"],
    "include_stdlib": false,
    "max_recursion_depth": 50,
    "enable_caching": true
  },
  "ast_analysis": {
    "include_stdlib": false,
    "include_external": false,
    "follow_symlinks": true,
    "case_sensitive": true,
    "use_stdlib_list": true
  },
  "visualization": {
    "image_format": "png",
    "image_dpi": 300,
    "layout_algorithm": "hierarchical",
    "color_scheme": "default",
    "max_nodes_display": 100,
    "hide_external_dependencies": true,
    "vis_network_source": "cdn"
  }
}
```

### Environment Variables

Set environment variables for API configuration:

```bash
# OpenAI API (if using OpenAI)
export OPENAI_API_KEY="your-api-key"

# Other LLM providers
export ANTHROPIC_API_KEY="your-api-key"
export COHERE_API_KEY="your-api-key"

# Proxy settings (if needed)
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
```

## Advanced Usage

### Working with Large Projects

For projects with 500+ files:

1. **Enable caching**:
   ```json
   {
     "dependency_analysis": {
       "enable_caching": true,
       "cache_dir": ".genai_docs_cache"
     }
   }
   ```

2. **Use parallel processing**:
   ```json
   {
     "orchestrator": {
       "parallel_documentation": true,
       "max_workers": 4
     }
   }
   ```

3. **Limit scope with ignore patterns**:
   ```json
   {
     "dependency_analysis": {
       "ignore_patterns": [
         "test_*",
         "*_test.py",
         "migrations/*",
         "vendor/*",
         "third_party/*"
       ]
     }
   }
   ```

### Handling Circular Dependencies

When circular dependencies are detected:

1. **Review the analysis report**:
   ```bash
   cat DEPENDENCY_ANALYSIS_REPORT.md
   ```

2. **Check visualization**:
   Open `dependency_analysis/dependency_graph.html` to see circular dependencies highlighted in red.

3. **Manual intervention** (if needed):
   - Refactor code to break unnecessary cycles
   - Use dependency injection patterns
   - Extract common functionality to separate modules

### Custom LLM Providers

To use a custom LLM provider, modify the main script or create a wrapper:

```python
# custom_llm.py
def custom_llm_provider(prompt):
    """Custom LLM implementation."""
    # Your custom logic here
    return "Generated documentation"

# Monkey patch the LLM function
import genai_docs.main
genai_docs.main.get_llm_documentation = custom_llm_provider
```

### Incremental Documentation

For large projects, you can document incrementally:

1. **Cache results**:
   ```json
   {"dependency_analysis": {"enable_caching": true}}
   ```

2. **Focus on changed files**:
   ```bash
   # Only document files modified in last 7 days
   find . -name "*.py" -mtime -7 | python -m genai_docs --files-from-stdin
   ```

## Understanding Output

### Generated Files

After running GenAI Docs, you'll find:

1. **Documentation files**:
   - `MODULE_NAME_DOCUMENTATION.md` for each module
   - `DOCUMENTATION.md` for packages

2. **Analysis report**:
   - `DEPENDENCY_ANALYSIS_REPORT.md` - Comprehensive dependency analysis

3. **Visualizations** (in `dependency_analysis/` directory):
   - `dependency_graph.png` - Static dependency graph image
   - `dependency_graph.html` - Interactive dependency explorer
   - `circular_dependencies/` - Focused circular dependency analysis

### Dependency Analysis Report

The report includes:

- **Executive Summary**: Key metrics and findings
- **Structural Analysis**: Architecture patterns and module categorization
- **Circular Dependencies**: Detailed analysis of any cycles found
- **Recommendations**: Actionable suggestions for improvement

### Interactive Visualization

The HTML visualization provides:

- **Node interaction**: Click nodes to see details
- **Search functionality**: Find specific modules
- **Layout options**: Switch between hierarchical, force-directed, and circular layouts
- **Cycle highlighting**: Toggle circular dependency visualization
- **Zoom and pan**: Navigate large graphs easily

## Troubleshooting

### Common Issues

#### 1. "No Python modules found"

**Cause**: GenAI Docs couldn't find Python files in the specified directory.

**Solutions**:
- Verify the path is correct
- Check that the directory contains `.py` files
- Ensure you have read permissions

#### 2. "Graphviz executable not found"

**Cause**: System Graphviz is not installed.

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt install graphviz

# macOS
brew install graphviz

# Windows - download from https://graphviz.org/download/
```

#### 3. "LLM API rate limit exceeded"

**Cause**: Too many API calls in a short time.

**Solutions**:
- Enable caching to reduce repeat calls
- Use parallel processing with lower worker count
- Implement custom retry logic with exponential backoff

#### 4. "Memory usage too high"

**Cause**: Large project overwhelming system memory.

**Solutions**:
- Increase system RAM or use a machine with more memory
- Use ignore patterns to exclude unnecessary files
- Enable incremental documentation for large codebases

#### 5. "Circular dependency documentation unclear"

**Cause**: Complex circular dependencies are hard to explain automatically.

**Solutions**:
- Review the cycle analysis in the dependency report
- Consider refactoring to break unnecessary cycles
- Manually edit generated documentation for clarity

### Debug Mode

Enable detailed logging:

```bash
python -m genai_docs --verbose --log-file debug.log
```

This creates a detailed log file showing:
- Import resolution decisions
- Graph construction steps
- Documentation generation progress
- Error details and stack traces

### Performance Tuning

#### Memory Optimization

```json
{
  "orchestrator": {
    "max_context_length": 2000,  // Reduce context size
    "context_summary_ratio": 0.2  // More aggressive summarization
  },
  "dependency_analysis": {
    "enable_caching": true,  // Cache results
    "max_recursion_depth": 20  // Limit recursion
  }
}
```

#### Speed Optimization

```json
{
  "orchestrator": {
    "parallel_documentation": true,
    "max_workers": 8  // Increase workers if you have CPU cores
  },
  "visualization": {
    "max_nodes_display": 50  // Limit visualization complexity
  }
}
```

## Best Practices

### Project Preparation

1. **Clean up your codebase**:
   - Remove unused imports
   - Fix syntax errors
   - Update import statements to be consistent

2. **Structure your project clearly**:
   - Use clear module and package naming
   - Organize related functionality together
   - Minimize circular dependencies

3. **Add basic docstrings**:
   - Even minimal docstrings help the LLM understand purpose
   - Focus on public APIs and complex logic

### Configuration Guidelines

1. **Start with defaults**: Use default settings for your first run
2. **Iteratively refine**: Adjust settings based on results
3. **Project-specific tuning**: Different projects may need different settings

### Workflow Integration

1. **CI/CD Integration**:
   ```yaml
   # .github/workflows/docs.yml
   name: Generate Documentation
   on: [push]
   jobs:
     docs:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Setup Python
           uses: actions/setup-python@v2
           with:
             python-version: 3.9
         - name: Install dependencies
           run: pip install genai-docs
         - name: Generate docs
           run: python -m genai_docs --project . --no-interactive
   ```

2. **Pre-commit hooks**:
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: genai-docs
           name: Update documentation
           entry: python -m genai_docs
           language: system
           files: '\.py$'
   ```

### Quality Assurance

1. **Review generated documentation**:
   - Check for accuracy and completeness
   - Verify that dependency context is helpful
   - Ensure explanations are clear

2. **Monitor dependency health**:
   - Review circular dependency reports
   - Track dependency complexity over time
   - Use insights to guide refactoring decisions

3. **Version control documentation**:
   - Commit generated documentation files
   - Track changes over time
   - Use diffs to understand how code changes affect documentation

---

*This user guide provides comprehensive instructions for installing, configuring, and using GenAI Docs effectively. For technical details about the system architecture and implementation, refer to the other documentation files in this repository.*
