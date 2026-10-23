"""Deterministic, zero-dependency subword tokenizer for offline testing."""

import re


class MockTokenizerAdapter:
    """Mock subword tokenizer simulating BPE subword fragmentation.

    - Clean, common words remain single tokens.
    - Runs of 3+ repeated characters or attached punctuation shatter into fragments.
    - Invariant: ''.join(tokenize(text_without_spaces)) reconstructs the text tokens.
    """

    def __init__(
        self,
        tokenizer_id: str = "mock-subword",
        family: str = "mock",
        vocab_size: int = 32000,
    ) -> None:
        self._tokenizer_id = tokenizer_id
        self._family = family
        self._vocab_size = vocab_size

    @property
    def tokenizer_id(self) -> str:
        return self._tokenizer_id

    @property
    def family(self) -> str:
        return self._family

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into simulated subwords."""
        if not text or not text.strip():
            return []

        # Split into words and whitespace-separated segments
        words = text.split()
        tokens: list[str] = []

        for word in words:
            # Check for attached punctuation at boundaries
            m = re.match(r"^([^\w\s]*)(.*?)([^\w\s]*)$", word, flags=re.UNICODE)
            if m:
                lead, core, trail = m.groups()
                for c in lead:
                    tokens.append(c)

                if core:
                    # Check for repeated character runs of length >= 3
                    if re.search(r"(.)\1{2,}", core):
                        # Fragment repeated word into chunks of max 2 characters
                        # e.g., 'iyaaaa' -> 'iya', 'aa', 'a'
                        # Find the run
                        run_match = re.search(r"((.)\2{2,})", core)
                        if run_match:
                            start, end = run_match.span()
                            prefix = core[:start]
                            run = core[start:end]
                            suffix = core[end:]

                            if prefix:
                                tokens.append(prefix)
                            # Split run into chunks of 2
                            for i in range(0, len(run), 2):
                                tokens.append(run[i : i + 2])
                            if suffix:
                                tokens.append(suffix)
                        else:
                            tokens.append(core)
                    elif len(core) > 10 and not core.startswith("http"):
                        # Long words split into 4-char chunks
                        for i in range(0, len(core), 4):
                            tokens.append(core[i : i + 4])
                    else:
                        tokens.append(core)

                for c in trail:
                    tokens.append(c)
            else:
                tokens.append(word)

        return tokens

    def count_tokens(self, text: str) -> int:
        """Count total simulated subword tokens."""
        return len(self.tokenize(text))
