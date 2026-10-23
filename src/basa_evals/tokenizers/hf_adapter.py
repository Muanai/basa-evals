"""Hugging Face AutoTokenizer adapter for IndoBERT, Mistral, and Gemma."""

from typing import Any


class HuggingFaceTokenizerAdapter:
    """Tokenizer adapter backed by Hugging Face transformers/tokenizers."""

    def __init__(
        self,
        tokenizer_id: str,
        pretrained_model_name: str,
        family: str = "wordpiece",
        trust_remote_code: bool = False,
    ) -> None:
        self._tokenizer_id = tokenizer_id
        self._pretrained_model_name = pretrained_model_name
        self._family = family

        try:
            from transformers import AutoTokenizer  # type: ignore[import-not-found]
        except ImportError as e:


            raise ImportError(
                f"The 'transformers' library is required to use tokenizer '{tokenizer_id}'. "
                f"Install it with: pip install basa-evals[tokenizers] (or pip install transformers)."
            ) from e

        self._tokenizer: Any = AutoTokenizer.from_pretrained(
            pretrained_model_name,
            use_fast=True,
            trust_remote_code=trust_remote_code,
        )

    @property
    def tokenizer_id(self) -> str:
        return self._tokenizer_id

    @property
    def family(self) -> str:
        return self._family

    @property
    def vocab_size(self) -> int:
        return len(self._tokenizer)

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into subword token strings."""
        if not text:
            return []
        tokens: list[str] = self._tokenizer.tokenize(text)
        return tokens

    def count_tokens(self, text: str) -> int:
        """Count subword tokens excluding special start/end markers."""
        if not text:
            return 0
        ids = self._tokenizer.encode(text, add_special_tokens=False)
        return len(ids)
