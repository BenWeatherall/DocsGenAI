import os
from pathlib import Path

import google.generativeai as genai

# --- Configuration ---
# Configure the Google Generative AI API.
# The API key should be set as an environment variable GOOGLE_API_KEY
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is required. "
        "Please set it with: export GOOGLE_API_KEY='your-api-key-here'"
    )
genai.configure(api_key=API_KEY)
MODEL_NAME = (
    "gemini-2.0-flash"  # Using gemini-2.0-flash as requested for text generation.
)


# --- ModuleNode Class ---
class ModuleNode:
    """
    Represents a single Python module (.py file) or package (directory with __init__.py)
    in the repository tree.
    """

    def __init__(self, path, name, is_package=False, is_root=False):
        self.path = path  # Full file system path to the module/package
        self.name = (
            name  # Name of the module or package (e.g., 'my_module', 'my_package')
        )
        self.is_package = (
            is_package  # True if it's a package, False if it's a single module file
        )
        self.is_root = is_root  # True if this is the root project node
        self.children = []  # List of child ModuleNode objects (sub-modules/sub-packages)
        self.content = None  # Stores the raw code content for .py files or __init__.py for packages
        self.documentation = None  # Stores the generated documentation from the LLM
        self.processed = False  # Flag to track if this node has been documented

    def add_child(self, child_node):
        """Adds a child module/package to this node."""
        self.children.append(child_node)

    def __repr__(self):
        """String representation for debugging."""
        return f"ModuleNode(name='{self.name}', is_package={self.is_package}, path='{self.path}')"


# --- File Reading Utilities ---
def read_project_files(project_path):
    """
    Read project-level files that provide context for the overall project.

    Args:
        project_path (str): Path to the project root

    Returns:
        dict: Dictionary containing project file contents
    """
    project_files = {}

    # Common project files to read
    files_to_read = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "README.md",
        "README.rst",
        "requirements.txt",
        "requirements-dev.txt",
        "Pipfile",
        "poetry.lock",
    ]

    for filename in files_to_read:
        file_path = Path(project_path) / filename
        if file_path.exists():
            try:
                with file_path.open(encoding="utf-8") as f:
                    project_files[filename] = f.read()
            except OSError as e:
                print(f"Warning: Could not read {filename}: {e}")
                project_files[filename] = f"# Error reading file: {e}"

    return project_files


def save_documentation_to_file(node, documentation):
    """
    Save the generated documentation to a markdown file in the module's directory.
    Handles multiple nodes in the same directory by using appropriate filenames.

    Args:
        node (ModuleNode): The node containing the module/package
        documentation (str): The generated documentation text
    """
    if not documentation or documentation.startswith("Error:"):
        print(f"Warning: No valid documentation to save for {node.name}")
        return

    # Determine the appropriate filename based on node type and context
    if node.is_package:
        # For packages, use the standard DOCUMENTATION.md filename
        doc_filename = "DOCUMENTATION.md"
    else:
        # For modules, check if the directory also contains a package (has __init__.py)
        # to avoid conflicts with package documentation
        dir_path = Path(node.path).parent
        if (dir_path / "__init__.py").exists():
            # This directory is also a package, so use a module-specific filename
            doc_filename = f"{node.name}_DOCUMENTATION.md"
        else:
            # Check if there are multiple .py files in this directory
            py_files = [
                f.name
                for f in dir_path.iterdir()
                if f.name.endswith(".py") and f.name != "__init__.py"
            ]
            if len(py_files) > 1:
                # Multiple modules in this directory, use module-specific filename
                doc_filename = f"{node.name}_DOCUMENTATION.md"
            else:
                # Single module in this directory, safe to use standard name
                doc_filename = "DOCUMENTATION.md"

    doc_path = Path(node.path) / doc_filename

    try:
        with doc_path.open("w", encoding="utf-8") as f:
            f.write(f"# {node.name} Documentation\n\n")
            f.write(documentation)
        print(f"Saved documentation to: {doc_path}")
    except OSError as e:
        print(f"Error saving documentation for {node.name}: {e}")


# --- Tree Building Logic ---
def build_module_tree(root_dir):
    """
    Recursively scans a given root directory to identify Python modules and packages,
    building a hierarchical ModuleNode tree.

    Args:
        root_dir (str): The absolute path to the root of the Python repository.

    Returns:
        ModuleNode: The root node of the module tree, or None if the directory is invalid.
    """
    root_dir = Path(root_dir).resolve()
    if not root_dir.is_dir():
        print(f"Error: Directory not found: {root_dir}")
        return None

    # Determine the base name for the root module/package.
    # If the root_dir itself is a package, its name is the directory name.
    # Otherwise, it's a container for top-level modules/packages.
    root_name = root_dir.name
    is_root_package = (root_dir / "__init__.py").exists()

    # Create the root node for the tree.
    # If the root_dir is a package, it's a package node.
    # If it's just a directory containing modules, it's a conceptual root.
    root_node = ModuleNode(
        str(root_dir), root_name, is_package=is_root_package, is_root=True
    )

    def _build_recursive(current_path, parent_node):
        """
        Helper function to recursively traverse directories and build the module tree.
        """
        for item in Path(current_path).iterdir():
            item_name = item.name
            item_path = item

            # Skip common non-source directories/files and hidden files.
            if item_name in [
                "__pycache__",
                ".git",
                ".venv",
                "venv",
                ".idea",
                ".DS_Store",
                "node_modules",
                "build",
                "dist",
                ".pytest_cache",
                ".mypy_cache",
            ] or item_name.startswith("."):
                continue

            if item_path.is_dir():
                # Check if it's a Python package (contains __init__.py)
                if (item_path / "__init__.py").exists():
                    module_name = item_name
                    node = ModuleNode(str(item_path), module_name, is_package=True)
                    parent_node.add_child(node)
                    # Recursively build for the new package
                    _build_recursive(str(item_path), node)
                else:
                    # It's a regular directory, recurse into it but attach children to the current parent.
                    # This handles cases where Python files are in subdirectories not marked as packages.
                    _build_recursive(str(item_path), parent_node)
            elif item_path.is_file() and item_name.endswith(".py"):
                # It's a Python module file
                if item_name == "__init__.py":
                    # __init__.py content is handled when its parent directory is identified as a package.
                    # We don't create a separate node for __init__.py itself as a module.
                    continue
                module_name = item_name[:-3]  # Remove .py extension to get module name
                node = ModuleNode(str(item_path), module_name, is_package=False)
                try:
                    with item_path.open(encoding="utf-8") as f:
                        node.content = f.read()
                except OSError as e:
                    print(f"Warning: Could not read file {item_path}: {e}")
                    node.content = f"# Error reading file: {e}"
                parent_node.add_child(node)

    # Start the recursive building process from the root directory
    _build_recursive(root_dir, root_node)
    return root_node


# --- LLM Documentation Logic ---
def get_llm_documentation(prompt):
    """
    Sends a prompt to the LLM (Gemini 2.0 Flash) and returns the generated documentation.
    Each call uses a fresh context window to prevent hallucinations from previous interactions.

    Args:
        prompt (str): The text prompt to send to the LLM.

    Returns:
        str: The generated documentation text, or an error message if the call fails.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        # Ensure a fresh context by providing only the current user prompt.
        response = model.generate_content(
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        # Access the text from the first candidate's first part
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            return response.candidates[0].content.parts[0].text
        return "Error: LLM response structure unexpected or empty."
    except (ConnectionError, TimeoutError, ValueError) as e:
        print(f"Error calling LLM for documentation: {e}")
        return f"Error: Could not generate documentation due to an API issue: {e}"


def document_project_root(node, project_files):
    """
    Generate documentation for the root project using project-level context files.

    Args:
        node (ModuleNode): The root project node
        project_files (dict): Dictionary containing project file contents

    Returns:
        str: Generated documentation for the project
    """
    print(f"Documenting: {node.name} (Project Root)")

    prompt_parts = []
    prompt_parts.append(
        f"Please provide clear, concise, and comprehensive documentation for the Python project '{node.name}'."
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

    # Include documentation of children (sub-modules/packages)
    if node.children:
        prompt_parts.append("\n## Sub-modules and Packages:\n")
        for child in node.children:
            if child.documentation:
                prompt_parts.append(f"\n### {child.name}\n")
                prompt_parts.append(child.documentation)
            else:
                prompt_parts.append(
                    f"\n### {child.name} (No documentation generated)\n"
                )
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
    return get_llm_documentation(full_prompt)


def document_module_tree_bottom_up(node, project_files=None):
    """
    Recursively documents the module tree from the leaves upwards.
    For each node, it first ensures its children are documented, then uses
    their documentation (not code) to inform its own documentation.

    Args:
        node (ModuleNode): The current module/package node to document.
        project_files (dict): Project-level files for root documentation

    Returns:
        str: The generated documentation for the current node.
    """
    if node.processed:
        return node.documentation

    # Step 1: Recursively document all children first (bottom-up approach)
    for child in node.children:
        document_module_tree_bottom_up(child, project_files)

    # Step 2: Now, document the current node
    print(f"Documenting: {node.name} (Path: {node.path})")

    # Special handling for root project
    if node.is_root:
        node.documentation = document_project_root(node, project_files or {})
    else:
        prompt_parts = []
        if node.is_package:
            # Prompt for a Python package
            prompt_parts.append(
                f"Please provide clear, concise, and comprehensive documentation for the Python package '{node.name}'."
            )
            prompt_parts.append("Your documentation should cover:")
            prompt_parts.append(
                "1.  **Purpose:** What is the overall goal or functionality of this package?"
            )
            prompt_parts.append(
                "2.  **Interface:** What are the main classes, functions, or variables exposed by this package for external use?"
            )
            prompt_parts.append(
                "3.  **Usage:** Provide clear examples of how this package would typically be imported and used."
            )
            prompt_parts.append(
                "4.  **Relationship to Sub-modules:** Explain how the sub-modules contribute to the package's overall functionality."
            )

            # Include documentation of children
            if node.children:
                prompt_parts.append(
                    "\nConsider the following as documentation for its direct sub-modules/sub-packages:"
                )
                for child in node.children:
                    if child.documentation:
                        prompt_parts.append(
                            f"\n--- Sub-module/Package: {child.name} Documentation ---\n"
                        )
                        prompt_parts.append(child.documentation)
                        prompt_parts.append(
                            "\n------------------------------------------------\n"
                        )
                    else:
                        prompt_parts.append(
                            f"\n--- Sub-module/Package: {child.name} (No documentation generated) ---\n"
                        )
            else:
                prompt_parts.append(
                    "\nThis package does not contain any direct sub-modules or sub-packages."
                )

            # Include content of __init__.py if it exists, as it often defines package-level interface.
            init_file_path = Path(node.path) / "__init__.py"
            if init_file_path.exists():
                try:
                    with init_file_path.open(encoding="utf-8") as f:
                        node.content = f.read()
                    prompt_parts.append(
                        f"\nHere is the content of the package's __init__.py file (if relevant to its interface or purpose):\n```python\n{node.content}\n```\n"
                    )
                except OSError as e:
                    print(f"Warning: Could not read __init__.py for {node.name}: {e}")
                    prompt_parts.append(
                        f"\nCould not read __init__.py for this package: {e}\n"
                    )
            else:
                prompt_parts.append(
                    "\nThis package does not have an __init__.py file with content that defines its interface.\n"
                )

        else:  # It's a regular .py module file (a leaf or an intermediate module)
            prompt_parts.append(
                f"Please provide clear, concise, and comprehensive documentation for the Python module '{node.name}'."
            )
            prompt_parts.append("Your documentation should cover:")
            prompt_parts.append(
                "1.  **Purpose:** What is the specific goal or functionality of this module?"
            )
            prompt_parts.append(
                "2.  **Interface:** What are the main functions, classes, or variables exposed by this module for external use?"
            )
            prompt_parts.append(
                "3.  **Usage:** Provide clear examples of how this module would typically be imported and used."
            )

            if node.content:
                prompt_parts.append(
                    f"\nHere is the Python code for the module:\n```python\n{node.content}\n```\n"
                )
            else:
                prompt_parts.append(
                    "\nThis module file is empty or its content could not be read.\n"
                )

        full_prompt = "\n".join(prompt_parts)
        node.documentation = get_llm_documentation(full_prompt)

    # Save documentation to file
    save_documentation_to_file(node, node.documentation)
    node.processed = True
    return node.documentation


# --- Main Execution ---
def main():
    """
    Main function to orchestrate the module tree building and documentation generation.
    """
    repo_path = input(
        "Please enter the absolute path to the Python repository you want to document: "
    )
    # Example for testing: repo_path = "/path/to/your/python_project"

    if not Path(repo_path).is_dir():
        print(f"Error: The provided path '{repo_path}' is not a valid directory.")
        return

    print(f"\nBuilding module tree for repository: {repo_path}")
    module_tree_root = build_module_tree(repo_path)

    if not module_tree_root:
        print("Failed to build the module tree. Exiting.")
        return

    # Read project-level files for root documentation
    print("Reading project configuration files...")
    project_files = read_project_files(repo_path)

    print("\nStarting documentation process (bottom-up, leaves first)...")
    # Document the entire tree starting from the conceptual root.
    # If the root_node itself is a package or contains children, proceed.
    if module_tree_root.is_package or module_tree_root.children:
        document_module_tree_bottom_up(module_tree_root, project_files)
    else:
        print(
            "No Python modules or packages found in the specified directory. Nothing to document."
        )
        return

    print("\n--- Documentation Complete ---")
    print("Generated Documentation Summary:")

    # Function to print documentation in a structured, hierarchical way
    def print_docs_summary(node, level=0):
        indent = "  " * level
        node_type = (
            "Project" if node.is_root else ("Package" if node.is_package else "Module")
        )
        print(f"{indent}- {node.name} ({node_type}):")
        if node.documentation:
            # Indent the documentation for better readability in the console output
            indented_doc = "\n".join(
                [indent + "  " + line for line in node.documentation.splitlines()]
            )
            print(f"{indented_doc}\n")
        else:
            print(f"{indent}  (No documentation generated for this node)")

        # Sort children by name for consistent output
        sorted_children = sorted(node.children, key=lambda c: c.name)
        for child in sorted_children:
            print_docs_summary(child, level + 1)

    print_docs_summary(module_tree_root)

    print("\nScript execution finished.")


# To run this script:
if __name__ == "__main__":
    main()
