"""Integrity assertions for the Pilot-210 benchmark slices."""

import json
from pathlib import Path

from basa_evals.core.schema import Sample


def test_pilot_210_integrity() -> None:
    repo_root = Path(__file__).parent.parent
    files = [
        repo_root / "data/gold/repetition_reduction_v1.jsonl",
        repo_root / "data/gold/slang_lexical_v1.jsonl",
        repo_root / "data/gold/abbreviation_phonetic_v1.jsonl",
        repo_root / "data/gold/typo_nonword_v1.jsonl",
        repo_root / "data/challenge/negative_controls_kbbi_v1.jsonl",
        repo_root / "data/challenge/negative_controls_code_switching_v1.jsonl",
        repo_root / "data/challenge/mixed_challenge_v1.jsonl",
    ]
    total = 0
    neg_count = 0
    ids: set[str] = set()

    for p in files:
        assert p.exists(), f"Missing file: {p}"
        pkg_copy = repo_root / "src/basa_evals" / p.relative_to(repo_root)
        assert pkg_copy.exists(), f"Missing packaged copy: {pkg_copy}"
        assert p.read_bytes() == pkg_copy.read_bytes(), f"Drift detected between {p} and {pkg_copy}"

        with open(p, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            assert len(lines) == 30, f"{p.name} must have 30 lines, found {len(lines)}"
            for line in lines:
                s = Sample.model_validate(json.loads(line))
                assert s.id not in ids, f"Duplicate id: {s.id}"
                ids.add(s.id)
                total += 1
                if s.negative_control:
                    neg_count += 1

    assert total == 210
    assert neg_count == 60
    assert neg_count / 180 >= 0.20  # Gated population >= 20%
    assert neg_count / 210 >= 0.20  # Total population >= 20%


def test_smsa_test_slice_integrity() -> None:
    repo_root = Path(__file__).parent.parent
    p = repo_root / "data/downstream/smsa_test_v1.jsonl"
    pkg_copy = repo_root / "src/basa_evals/data/downstream/smsa_test_v1.jsonl"

    assert p.exists(), f"Missing dataset: {p}"
    assert pkg_copy.exists(), f"Missing package copy: {pkg_copy}"
    assert p.read_bytes() == pkg_copy.read_bytes(), "Drift between root and packaged slice"

    with open(p, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) == 150, f"Expected 150 rows, got {len(lines)}"

    class_counts: dict[str, int] = {}
    ids: set[str] = set()

    for line in lines:
        data = json.loads(line)
        sample = Sample.model_validate(data)
        assert sample.id not in ids, f"Duplicate id: {sample.id}"
        ids.add(sample.id)
        assert sample.gold_label is not None
        class_counts[sample.gold_label] = class_counts.get(sample.gold_label, 0) + 1

    assert class_counts.get("positive") == 50
    assert class_counts.get("neutral") == 50
    assert class_counts.get("negative") == 50

