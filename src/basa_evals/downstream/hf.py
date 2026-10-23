from typing import Any


class HuggingFaceSentimentClassifier:
    """Wrapper around HuggingFace transformers sequence classification pipeline."""

    classifier_id: str
    task: str = "sentiment"
    classes: list[str] = ["positive", "neutral", "negative"]

    def __init__(
        self,
        classifier_id: str,
        model_name: str,
        label_mapping: dict[str, str] | None = None,
        device: int | str = -1,
        **pipeline_kwargs: Any,
    ) -> None:
        self.classifier_id = classifier_id
        self.model_name = model_name
        self.label_mapping = label_mapping or {
            "label_0": "positive",
            "label_1": "neutral",
            "label_2": "negative",
            "positive": "positive",
            "neutral": "neutral",
            "negative": "negative",
            "positif": "positive",
            "netral": "neutral",
            "negatif": "negative",
        }

        try:
            import transformers  # type: ignore[import-not-found]
        except ImportError as e:
            raise ImportError(
                f"The 'transformers' library is required to use HuggingFace classifier '{classifier_id}'. "
                f"Install it with: pip install basa-evals[downstream] (or pip install transformers torch)."
            ) from e

        self._pipeline = transformers.pipeline(
            "text-classification",
            model=model_name,
            device=device,
            **pipeline_kwargs,
        )

    def _normalize_label(self, raw_label: str) -> str:
        clean = raw_label.strip().lower()
        return self.label_mapping.get(clean, clean)

    def predict(self, text: str) -> str:
        res = self._pipeline(text, truncation=True)
        raw_label = res[0]["label"]
        return self._normalize_label(raw_label)

    def predict_batch(self, texts: list[str]) -> list[str]:
        results = self._pipeline(texts, truncation=True, batch_size=32)
        return [self._normalize_label(r["label"]) for r in results]
