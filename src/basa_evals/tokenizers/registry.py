"""Registry for discovery and resolution of subword tokenizer adapters."""

from collections.abc import Callable

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

    def register_defaults(self) -> None:
        """Register default offline and lazy-factory tokenizers."""
        from basa_evals.tokenizers.mock import MockTokenizerAdapter

        self.register(MockTokenizerAdapter())

        def _make_gpt4o() -> TokenizerAdapter:
            from basa_evals.tokenizers.tiktoken_adapter import TiktokenAdapter

            return TiktokenAdapter("gpt-4o", encoding_name="o200k_base")

        def _make_llama3() -> TokenizerAdapter:
            try:
                from basa_evals.tokenizers.hf_adapter import HuggingFaceTokenizerAdapter

                return HuggingFaceTokenizerAdapter(
                    "llama-3",
                    pretrained_model_name="meta-llama/Meta-Llama-3-8B",
                    family="bpe",
                )
            except Exception:
                from basa_evals.tokenizers.tiktoken_adapter import TiktokenAdapter

                return TiktokenAdapter("llama-3", encoding_name="cl100k_base")

        def _make_indobert() -> TokenizerAdapter:
            from basa_evals.tokenizers.hf_adapter import HuggingFaceTokenizerAdapter

            return HuggingFaceTokenizerAdapter(
                "indobert",
                pretrained_model_name="indobenchmark/indobert-base-p1",
                family="wordpiece",
            )

        def _make_gemma2() -> TokenizerAdapter:
            from basa_evals.tokenizers.hf_adapter import HuggingFaceTokenizerAdapter

            return HuggingFaceTokenizerAdapter(
                "gemma-2",
                pretrained_model_name="google/gemma-2-2b",
                family="sentencepiece",
            )

        self.register_factory("gpt-4o", _make_gpt4o)
        self.register_factory("llama-3", _make_llama3)
        self.register_factory("indobert", _make_indobert)
        self.register_factory("gemma-2", _make_gemma2)
