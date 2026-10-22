"""Simple regex and dictionary ablation baseline adapter."""

import json
from pathlib import Path
import re


class SimpleRegexBaseline:
    """Ablation baseline applying run collapse (>=3) and 50-entry dictionary lookup."""

    def __init__(
        self,
        system_id: str = "simple-regex",
        dict_path: str | Path | None = None,
        **kwargs: object,
    ) -> None:
        self._system_id = system_id
        if dict_path is None:
            dict_path = (
                Path(__file__).parent.parent / "data" / "baselines" / "simple_regex_dict_v1.json"
            )
        with open(dict_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.mappings: dict[str, str] = data.get("mappings", {})

        # Precompile word boundary regex for fast dictionary replacement
        if self.mappings:
            escaped = [re.escape(k) for k in self.mappings.keys()]
            self._pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b")
        else:
            self._pattern = None

    @property
    def system_id(self) -> str:
        return self._system_id

    @property
    def version(self) -> str | None:
        return "1.0.0"

    def process(self, text: str) -> str:
        # 1. Lowercase
        t = text.lower()
        # 2. Collapse runs of >= 3 identical characters to 1
        t = re.sub(r"(.)\1{2,}", r"\1", t)
        # 3. Apply dictionary replacement
        if self._pattern:
            t = self._pattern.sub(lambda m: self.mappings[m.group(0)], t)
        return t

    def process_batch(self, texts: list[str]) -> list[str]:
        return [self.process(t) for t in texts]
