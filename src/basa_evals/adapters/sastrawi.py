"""Sastrawi morphological stemmer adapter."""

import importlib.metadata
from typing import Any


class SastrawiAdapter:
    """Stemmer baseline using PySastrawi.

    Morphological stemmer, not a normalizer — included as a destructive-edit
    stress baseline, not as a competitive normalizer.
    """

    def __init__(self, system_id: str = "sastrawi", **kwargs: Any) -> None:
        self._system_id = system_id
        try:
            from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

            self._stemmer = StemmerFactory().create_stemmer()
        except ImportError as e:
            raise ImportError(
                "PySastrawi is required for SastrawiAdapter. "
                "Install via `pip install basa-evals[sastrawi]` or `pip install PySastrawi`."
            ) from e

    @property
    def system_id(self) -> str:
        return self._system_id

    @property
    def version(self) -> str | None:
        try:
            return importlib.metadata.version("PySastrawi")
        except Exception:
            return None

    def process(self, text: str) -> str:
        return self._stemmer.stem(text)

    def process_batch(self, texts: list[str]) -> list[str]:
        return [self.process(t) for t in texts]
