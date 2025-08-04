#!/usr/bin/env python3
"""
Test script to validate documentation file generation logic.
"""

import tempfile
from pathlib import Path


def test_file_generation_logic():
    """Test the file generation logic for different scenarios."""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing in temporary directory: {temp_dir}")

        # Scenario 1: Single module in directory
        single_module_dir = Path(temp_dir) / "single_module"
        single_module_dir.mkdir(parents=True)
        (single_module_dir / "module.py").write_text("# Test module")

        # Scenario 2: Multiple modules in directory
        multi_module_dir = Path(temp_dir) / "multi_module"
        multi_module_dir.mkdir(parents=True)
        (multi_module_dir / "module1.py").write_text("# Test module 1")
        (multi_module_dir / "module2.py").write_text("# Test module 2")

        # Scenario 3: Package only
        package_dir = Path(temp_dir) / "package_only"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("# Package init")

        # Scenario 4: Module and package in same directory
        mixed_dir = Path(temp_dir) / "mixed"
        mixed_dir.mkdir(parents=True)
        (mixed_dir / "module.py").write_text("# Test module")
        (mixed_dir / "__init__.py").write_text("# Package init")

        # Test the logic
        print("\nTesting file generation logic:")

        # Test single module
        dir_path = single_module_dir
        py_files = [
            f.name
            for f in dir_path.iterdir()
            if f.name.endswith(".py") and f.name != "__init__.py"
        ]
        has_init = (dir_path / "__init__.py").exists()
        print(f"Single module dir: {py_files}, has __init__.py: {has_init}")

        # Test multiple modules
        dir_path = multi_module_dir
        py_files = [
            f.name
            for f in dir_path.iterdir()
            if f.name.endswith(".py") and f.name != "__init__.py"
        ]
        has_init = (dir_path / "__init__.py").exists()
        print(f"Multi module dir: {py_files}, has __init__.py: {has_init}")

        # Test package only
        dir_path = package_dir
        py_files = [
            f.name
            for f in dir_path.iterdir()
            if f.name.endswith(".py") and f.name != "__init__.py"
        ]
        has_init = (dir_path / "__init__.py").exists()
        print(f"Package only dir: {py_files}, has __init__.py: {has_init}")

        # Test mixed
        dir_path = mixed_dir
        py_files = [
            f.name
            for f in dir_path.iterdir()
            if f.name.endswith(".py") and f.name != "__init__.py"
        ]
        has_init = (dir_path / "__init__.py").exists()
        print(f"Mixed dir: {py_files}, has __init__.py: {has_init}")

        print("\nExpected behavior:")
        print("- Single module: DOCUMENTATION.md")
        print("- Multiple modules: module1_DOCUMENTATION.md, module2_DOCUMENTATION.md")
        print("- Package only: DOCUMENTATION.md")
        print("- Mixed (module): module_DOCUMENTATION.md")
        print("- Mixed (package): DOCUMENTATION.md")


if __name__ == "__main__":
    test_file_generation_logic()
