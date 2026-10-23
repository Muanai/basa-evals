import pytest

from basa_evals.downstream.base import ClassifierAdapter
from basa_evals.downstream.mock import MockSentimentClassifier
from basa_evals.downstream.registry import ClassifierRegistry


def test_mock_sentiment_classifier_behavior() -> None:
    clf = MockSentimentClassifier()
    assert isinstance(clf, ClassifierAdapter)
    assert clf.classifier_id == "mock-sentiment"
    assert clf.task == "sentiment"
    assert clf.classes == ["positive", "neutral", "negative"]

    # Raw slang/elongated vs normalized
    assert clf.predict("pelayanan sangat ramah dan memuaskan") == "positive"
    assert clf.predict("produk jelek dan rusak parah") == "negative"
    assert clf.predict("hari ini saya pergi ke kantor") == "neutral"

    # Batch prediction
    preds = clf.predict_batch(["bagus sekali", "jelek", "biasa saja"])
    assert preds == ["positive", "negative", "neutral"]


def test_hf_sentiment_classifier_import_guard() -> None:
    from basa_evals.downstream.hf import HuggingFaceSentimentClassifier

    try:
        import transformers  # type: ignore[import-not-found]  # noqa: F401

        has_hf = True
    except ImportError:
        has_hf = False

    if not has_hf:
        with pytest.raises(ImportError) as exc_info:
            HuggingFaceSentimentClassifier("indobert-smsa", model_name="wirasana/indobert-sentiment-smsa")
        assert "pip install" in str(exc_info.value) or "downstream" in str(exc_info.value)


def test_classifier_registry() -> None:
    registry = ClassifierRegistry()
    registry.register_defaults()
    available = registry.list_available()
    assert "mock-sentiment" in available
    assert "indobert-smsa" in available

    clf = registry.get("mock-sentiment")
    assert clf.classifier_id == "mock-sentiment"
