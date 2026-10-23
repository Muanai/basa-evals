from collections.abc import Callable

from basa_evals.downstream.base import ClassifierAdapter
from basa_evals.downstream.mock import MockSentimentClassifier


class ClassifierRegistry:
    """Registry for downstream classifier models."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], ClassifierAdapter]] = {}
        self._instances: dict[str, ClassifierAdapter] = {}

    def register(self, classifier: ClassifierAdapter) -> None:
        """Register a pre-constructed classifier instance."""
        self._instances[classifier.classifier_id] = classifier

    def register_factory(
        self, classifier_id: str, factory: Callable[[], ClassifierAdapter]
    ) -> None:
        """Register a lazy constructor factory for a classifier."""
        self._factories[classifier_id] = factory

    def register_defaults(self) -> None:
        """Register default supported downstream classifiers."""
        self.register(MockSentimentClassifier("mock-sentiment"))

        def create_indobert_smsa() -> ClassifierAdapter:
            from basa_evals.downstream.hf import HuggingFaceSentimentClassifier

            return HuggingFaceSentimentClassifier(
                classifier_id="indobert-smsa",
                model_name="wirasana/indobert-sentiment-smsa",
            )

        self.register_factory("indobert-smsa", create_indobert_smsa)
        self.register_factory("hf-smsa", create_indobert_smsa)

    def get(self, classifier_id: str) -> ClassifierAdapter:
        """Resolve a classifier by ID, instantiating via factory if necessary."""
        if classifier_id in self._instances:
            return self._instances[classifier_id]

        if classifier_id in self._factories:
            instance = self._factories[classifier_id]()
            self._instances[classifier_id] = instance
            return instance

        raise KeyError(
            f"Classifier '{classifier_id}' not found in registry. "
            f"Available classifiers: {self.list_available()}"
        )

    def list_available(self) -> list[str]:
        """List all available registered classifier identifiers."""
        keys = set(self._instances.keys()) | set(self._factories.keys())
        return sorted(keys)
