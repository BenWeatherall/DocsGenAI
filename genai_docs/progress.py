"""
Progress tracking for documentation generation.

This module provides a simple progress tracker that displays
documentation generation progress without external dependencies.
"""

import logging
import sys

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Simple progress tracker for documentation generation."""

    def __init__(self, total: int, enabled: bool = True) -> None:
        """
        Initialize the progress tracker.

        Args:
            total: Total number of items to process
            enabled: Whether progress tracking is enabled
        """
        self.total = total
        self.current = 0
        self.enabled = enabled
        self.last_module: str | None = None

    def update(self, module_name: str, increment: int = 1) -> None:
        """
        Update progress.

        Args:
            module_name: Name of the module being processed
            increment: Number of items completed
        """
        self.current += increment
        self.last_module = module_name

        if self.enabled:
            percentage = (self.current / self.total * 100) if self.total > 0 else 0
            bar_length = 40
            filled = (
                int(bar_length * self.current / self.total) if self.total > 0 else 0
            )
            bar = "=" * filled + "-" * (bar_length - filled)

            # Print progress bar
            sys.stdout.write(
                f"\r[{bar}] {self.current}/{self.total} ({percentage:.1f}%) - {module_name}"
            )
            sys.stdout.flush()

            # Print newline when complete
            if self.current >= self.total:
                sys.stdout.write("\n")
                sys.stdout.flush()

    def finish(self) -> None:
        """Mark progress as complete."""
        if self.enabled and self.current < self.total:
            self.update(self.last_module or "Complete", self.total - self.current)
