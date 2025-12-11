"""
Caching system for documentation generation.

This module provides caching functionality to avoid regenerating documentation
for unchanged modules, improving performance and reducing API costs.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentationCache:
    """Manages caching of generated documentation."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the documentation cache.

        Args:
            cache_dir: Directory to store cache files (default: .genai-docs in project root)
        """
        self.cache_dir = cache_dir
        self.cache_file: Optional[Path] = None
        self.cache_data: dict[str, dict[str, any]] = {}

    def initialize(self, project_root: Path) -> None:
        """
        Initialize the cache for a project.

        Args:
            project_root: Root directory of the project
        """
        if self.cache_dir is None:
            self.cache_dir = project_root / ".genai-docs"
        else:
            self.cache_dir = Path(self.cache_dir).resolve()

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"

        # Load existing cache
        if self.cache_file.exists():
            try:
                with self.cache_file.open("r", encoding="utf-8") as f:
                    self.cache_data = json.load(f)
                logger.debug(f"Loaded cache with {len(self.cache_data)} entries")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache_data = {}
        else:
            self.cache_data = {}

    def get_file_hash(self, file_path: Path) -> str:
        """
        Calculate hash of a file's content and metadata.

        Args:
            file_path: Path to the file

        Returns:
            SHA256 hash of file content and modification time
        """
        if not file_path.exists():
            return ""

        try:
            stat = file_path.stat()
            # Include modification time and size in hash
            with file_path.open("rb") as f:
                content = f.read()
            hash_input = f"{content}{stat.st_mtime}{stat.st_size}".encode()
            return hashlib.sha256(hash_input).hexdigest()
        except OSError as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""

    def is_cached(self, module_path: str, file_path: Path) -> bool:
        """
        Check if documentation for a module is cached and up-to-date.

        Args:
            module_path: Path identifier for the module
            file_path: Path to the source file

        Returns:
            True if cached documentation exists and is current
        """
        if module_path not in self.cache_data:
            return False

        cached_entry = self.cache_data[module_path]
        cached_hash = cached_entry.get("hash", "")

        # Check if file still exists and hash matches
        if not file_path.exists():
            return False

        current_hash = self.get_file_hash(file_path)
        return cached_hash == current_hash and cached_hash != ""

    def get_cached_documentation(self, module_path: str) -> Optional[str]:
        """
        Get cached documentation for a module.

        Args:
            module_path: Path identifier for the module

        Returns:
            Cached documentation string, or None if not cached
        """
        if module_path not in self.cache_data:
            return None

        return self.cache_data[module_path].get("documentation")

    def cache_documentation(
        self, module_path: str, file_path: Path, documentation: str
    ) -> None:
        """
        Cache documentation for a module.

        Args:
            module_path: Path identifier for the module
            file_path: Path to the source file
            documentation: Generated documentation to cache
        """
        file_hash = self.get_file_hash(file_path)
        self.cache_data[module_path] = {
            "hash": file_hash,
            "documentation": documentation,
            "file_path": str(file_path),
        }

        # Save cache to disk
        self._save_cache()

    def _save_cache(self) -> None:
        """Save cache data to disk."""
        if not self.cache_file:
            return

        try:
            with self.cache_file.open("w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def clear_cache(self, module_path: Optional[str] = None) -> None:
        """
        Clear cache entries.

        Args:
            module_path: Specific module path to clear, or None to clear all
        """
        if module_path:
            self.cache_data.pop(module_path, None)
        else:
            self.cache_data.clear()

        self._save_cache()

    def get_cache_stats(self) -> dict[str, int]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "total_entries": len(self.cache_data),
            "cache_file": str(self.cache_file) if self.cache_file else None,
        }
