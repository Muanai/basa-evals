"""Integrity assertions for the Pilot-210 benchmark slices."""

import json
from pathlib import Path

from basa_evals.core.schema import Sample


def test_pilot_210_integrity():
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
