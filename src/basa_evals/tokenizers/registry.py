"""Registry for discovery and resolution of subword tokenizer adapters."""

from typing import Callable
from basa_evals.tokenizers.base import TokenizerAdapter


class TokenizerRegistry:
    """Registry maintaining available subword tokenizer adapters."""

    def __init__(self) -> None:
        self._tokenizers: dict[str, TokenizerAdapter] = {}
        self._factories: dict[str, Callable[[], TokenizerAdapter]] = {}

    def register(self, tokenizer: TokenizerAdapter) -> None:
        """Register an instantiated TokenizerAdapter."""
        if not isinstance(tokenizer, TokenizerAdapter):
            raise TypeError(f"Object {tokenizer} does not implement TokenizerAdapter protocol.")
        self._tokenizers[tokenizer.tokenizer_id] = tokenizer

    def register_factory(self, tokenizer_id: str, factory: Callable[[], TokenizerAdapter]) -> None:
        """Register a lazy factory for a TokenizerAdapter."""
        self._factories[tokenizer_id] = factory

    def get(self, tokenizer_id: str) -> TokenizerAdapter:
        """Retrieve a tokenizer by its unique identifier."""
        if tokenizer_id in self._tokenizers:
            return self._tokenizers[tokenizer_id]

        if tokenizer_id in self._factories:
            tok = self._factories[tokenizer_id]()
            self._tokenizers[tokenizer_id] = tok
            return tok

        raise KeyError(
            f"Tokenizer '{tokenizer_id}' is not registered. Available: {self.list_available()}"
        )

    def list_available(self) -> list[str]:
        """List all registered and lazy factory tokenizer identifiers."""
        return sorted(set(self._tokenizers.keys()) | set(self._factories.keys()))

    def clear(self) -> None:
        """Clear all registered tokenizers."""
        self._tokenizers.clear()
        self._factories.clear()
