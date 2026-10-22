"""BasePreprocessor protocol definition for Systems Under Test."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class BasePreprocessor(Protocol):
    """Protocol defining the interface for all Systems Under Test."""

    @property
    def system_id(self) -> str:
        """Unique identifier of the system."""
        ...

    @property
    def version(self) -> str | None:
        """Version of the underlying library or implementation, or None."""
        ...

    def process(self, text: str) -> str:
        """Process a single text sample."""
        ...

    def process_batch(self, texts: list[str]) -> list[str]:
        """Process a batch of texts, preserving exact order and length."""
        ...
