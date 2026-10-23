"""Abstract protocol definition for evaluated subword tokenizers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenizerAdapter(Protocol):
    """Protocol satisfied by all subword tokenizers evaluated in Tier 2."""

    @property
    def tokenizer_id(self) -> str:
        """Unique identifier (e.g. 'gpt-4o', 'llama-3', 'indobert', 'mistral-7b')."""
        ...

    @property
    def family(self) -> str:
        """Subword algorithm family (e.g. 'bpe', 'wordpiece', 'sentencepiece')."""
        ...

    @property
    def vocab_size(self) -> int:
        """Total vocabulary size."""
        ...

    def tokenize(self, text: str) -> list[str]:
        """Convert input string into a list of subword token strings."""
        ...

    def count_tokens(self, text: str) -> int:
        """Optimized calculation of total subword token count."""
        ...
