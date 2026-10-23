"""Tiktoken-backed subword tokenizer adapter for OpenAI and BPE models."""

from typing import Any


class TiktokenAdapter:
    """Tokenizer adapter backed by OpenAI's tiktoken library."""

    def __init__(
        self,
        tokenizer_id: str = "gpt-4o",
        encoding_name: str = "o200k_base",
    ) -> None:
        self._tokenizer_id = tokenizer_id
        self._family = "bpe"
        self._encoding_name = encoding_name

        try:
            import tiktoken
        except ImportError as e:
            raise ImportError(
                f"The 'tiktoken' library is required to use tokenizer '{tokenizer_id}'. "
                f"Install it with: pip install basa-evals[tokenizers] (or pip install tiktoken)."
            ) from e

        try:
            self._encoding: Any = tiktoken.get_encoding(encoding_name)
        except Exception:
            self._encoding = tiktoken.encoding_for_model(tokenizer_id)

    @property
    def tokenizer_id(self) -> str:
        return self._tokenizer_id

    @property
    def family(self) -> str:
        return self._family

    @property
    def vocab_size(self) -> int:
        return int(self._encoding.n_vocab)

    def tokenize(self, text: str) -> list[str]:
        """Encode text and decode individual token IDs into subword strings."""
        if not text:
            return []
        token_ids: list[int] = self._encoding.encode(text, allowed_special="all")
        result: list[str] = []
        for tid in token_ids:
            try:
                b = self._encoding.decode_single_token_bytes(tid)
                result.append(b.decode("utf-8", errors="replace"))
            except Exception:
                result.append(str(tid))
        return result

    def count_tokens(self, text: str) -> int:
        """Fast path token count computation."""
        if not text:
            return 0
        return len(self._encoding.encode(text, allowed_special="all"))
