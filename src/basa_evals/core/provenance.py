"""Provenance utilities for dataset hashing and Git revision tracking."""

import hashlib
import subprocess
from pathlib import Path


def compute_file_sha256(path: Path) -> str:
    """Compute hex-encoded SHA-256 digest of a file in streaming chunks."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_git_commit() -> str | None:
    """Resolve current Git commit HEAD hash, or None if outside git or failed.

    This function must never raise an exception.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            commit = res.stdout.strip()
            if len(commit) == 40:
                return commit
    except Exception:
        pass
    return None
