import re

POSITIVE_KEYWORDS: set[str] = {
    "bagus",
    "senang",
    "mantap",
    "puas",
    "keren",
    "suka",
    "enak",
    "ramah",
    "cepat",
    "membantu",
    "indah",
    "rapi",
    "bersih",
    "hebat",
    "berkualitas",
    "memuaskan",
    "terbaik",
    "rekomendasi",
    "lezat",
    "nikmat",
}

NEGATIVE_KEYWORDS: set[str] = {
    "jelek",
    "kecewa",
    "rusak",
    "buruk",
    "benci",
    "marah",
    "parah",
    "rugi",
    "lambat",
    "lelet",
    "kapok",
    "batal",
    "salah",
    "palsu",
    "kasar",
    "menyesal",
    "hancur",
    "payah",
    "tumpah",
    "basi",
}


class MockSentimentClassifier:
    """Deterministic, zero-dependency sentiment classifier heuristic for hermetic testing."""

    classifier_id: str = "mock-sentiment"
    task: str = "sentiment"
    classes: list[str] = ["positive", "neutral", "negative"]

    def __init__(self, classifier_id: str = "mock-sentiment") -> None:
        self.classifier_id = classifier_id

    def predict(self, text: str) -> str:
        words = re.findall(r"\w+", text.lower())
        pos_score = sum(1 for w in words if w in POSITIVE_KEYWORDS)
        neg_score = sum(1 for w in words if w in NEGATIVE_KEYWORDS)

        if pos_score > neg_score:
            return "positive"
        if neg_score > pos_score:
            return "negative"
        return "neutral"

    def predict_batch(self, texts: list[str]) -> list[str]:
        return [self.predict(t) for t in texts]
