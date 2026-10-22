"""Tests for provenance tracking, slice resolution, and suite loading."""

from pathlib import Path
import pytest
from basa_evals.core.loader import resolve_slice, load_suite
from basa_evals.core.provenance import compute_file_sha256, get_git_commit


def test_resolve_slice_package_data():
    resolved = resolve_slice("gold/slang_lexical_v1.jsonl")
    assert resolved.exists()
    assert resolved.is_file()


def test_load_pilot_suite():
    repo_root = Path(__file__).parent.parent
    suite_cfg, slices_data = load_suite(repo_root / "configs/suites/pilot_210.yaml")
    assert suite_cfg.name == "pilot_210"
    assert len(slices_data) == 7
    total_samples = sum(len(samples) for _, samples in slices_data)
    assert total_samples == 210


def test_provenance_sha():
    resolved = resolve_slice("gold/slang_lexical_v1.jsonl")
    h = compute_file_sha256(resolved)
    assert len(h) == 64
    assert isinstance(h, str)


def test_git_commit():
    commit = get_git_commit()
    # Inside git repo, this should return a 40-char sha string
    assert commit is not None
    assert len(commit) == 40
