"""Suite and dataset loader with robust resource resolution."""

import importlib.resources
import json
from pathlib import Path
from typing import Any
import yaml
from basa_evals.core.schema import RunConfig, Sample, SliceConfig


def resolve_slice(path: str | Path) -> Path:
    """Resolve a slice path against filesystem, repository data, or packaged package data."""
    p = Path(path)
    if p.is_absolute() and p.exists() and p.is_file():
        return p

    # Check relative to current working directory
    if p.exists() and p.is_file():
        return p.resolve()

    # Check relative to "data" directory in CWD or repo root
    cwd_data = Path("data") / p
    if cwd_data.exists() and cwd_data.is_file():
        return cwd_data.resolve()

    # Check relative to module directory
    module_data = Path(__file__).parent.parent / "data" / p
    if module_data.exists() and module_data.is_file():
        return module_data.resolve()

    # Check via importlib.resources
    try:
        parts = p.parts
        res = importlib.resources.files("basa_evals.data").joinpath(*parts)
        candidate = Path(str(res))
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    except Exception:
        pass

    raise FileNotFoundError(f"Could not resolve slice file: '{path}'")


def resolve_suite_path(suite_path: str | Path) -> Path:
    """Resolve a suite YAML path by direct file path or known suite name."""
    p = Path(suite_path)
    if p.is_file():
        return p.resolve()

    # If suite name without extension (e.g. 'pilot_210')
    name = p.stem
    candidates = [
        Path(f"configs/suites/{name}.yaml"),
        Path(f"configs/suites/{name}.yml"),
        Path(__file__).parent.parent / "configs" / "suites" / f"{name}.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    # Package resources
    try:
        res = importlib.resources.files("basa_evals.configs.suites").joinpath(f"{name}.yaml")
        candidate = Path(str(res))
        if candidate.is_file():
            return candidate.resolve()
    except Exception:
        pass

    raise FileNotFoundError(f"Could not resolve suite configuration: '{suite_path}'")


def load_suite(
    suite_path: str | Path,
) -> tuple[RunConfig, list[tuple[SliceConfig, list[Sample]]]]:
    """Load and validate a suite YAML and all its constituent dataset slices."""
    path = resolve_suite_path(suite_path)
    with open(path, "r", encoding="utf-8") as f:
        raw_cfg: dict[str, Any] = yaml.safe_load(f)

    run_config = RunConfig.model_validate(raw_cfg)
    slices_data: list[tuple[SliceConfig, list[Sample]]] = []

    for slice_cfg in run_config.slices:
        slice_file = resolve_slice(slice_cfg.path)
        samples: list[Sample] = []
        with open(slice_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                s = Sample.model_validate(json.loads(line))
                if s.dataset_version != run_config.dataset_version:
                    raise ValueError(
                        f"Sample '{s.id}' in '{slice_file.name}' specifies dataset_version "
                        f"'{s.dataset_version}', expected '{run_config.dataset_version}'."
                    )
                if s.slice != slice_cfg.slice_name:
                    raise ValueError(
                        f"Sample '{s.id}' in '{slice_file.name}' declares slice '{s.slice}', "
                        f"expected '{slice_cfg.slice_name}'."
                    )
                samples.append(s)

        slices_data.append((slice_cfg, samples))

    return run_config, slices_data
