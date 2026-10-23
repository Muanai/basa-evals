from typing import Protocol, runtime_checkable


@runtime_checkable
class ClassifierAdapter(Protocol):
    """Protocol for downstream classification models evaluated in basa-evals."""

    classifier_id: str
    task: str
    classes: list[str]

    def predict(self, text: str) -> str:
        """Predict the target class for a single input text."""
        ...

    def predict_batch(self, texts: list[str]) -> list[str]:
        """Predict target classes for a batch of input texts."""
        ...
