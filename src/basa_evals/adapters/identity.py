"""Identity adapter acting as noise floor and no-op control."""


class RawAdapter:
    """Identity preprocessor returning input strings unmodified."""

    def __init__(self, system_id: str = "raw-identity", **kwargs: object) -> None:
        self._system_id = system_id

    @property
    def system_id(self) -> str:
        return self._system_id

    @property
    def version(self) -> str | None:
        return None

    def process(self, text: str) -> str:
        return text

    def process_batch(self, texts: list[str]) -> list[str]:
        return list(texts)
