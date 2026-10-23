"""Tests for System Under Test adapters, registry, and baseline implementations."""

import pytest

from basa_evals.adapters.basa import BasaAdapter
from basa_evals.adapters.base import BasePreprocessor
from basa_evals.adapters.identity import RawAdapter
from basa_evals.adapters.sastrawi import SastrawiAdapter
from basa_evals.adapters.simple_regex import SimpleRegexBaseline
from basa_evals.core.registry import Registry


def test_raw_adapter_conforms() -> None:
    adapter = RawAdapter()
    assert isinstance(adapter, BasePreprocessor)
    assert adapter.system_id == "raw-identity"
    assert adapter.version is None
    assert adapter.process("Aplikasi Kafka") == "Aplikasi Kafka"
    assert adapter.process_batch(["a", "b"]) == ["a", "b"]


def test_simple_regex_ablation() -> None:
    adapter = SimpleRegexBaseline()
    assert isinstance(adapter, BasePreprocessor)
    assert adapter.system_id == "simple-regex"
    res = adapter.process("iyaaaaa gw mau")
    assert "saya" in res


def test_registry_resolution() -> None:
    adapter = Registry.get("raw", system_id="custom-raw")
    assert adapter.system_id == "custom-raw"
    assert isinstance(adapter, BasePreprocessor)


def test_basa_adapter_valid_params() -> None:
    adapter = BasaAdapter(
        system_id="basa-default",
        params={"lowercase": True, "apply_slang": True, "apply_typo": False},
    )
    assert isinstance(adapter, BasePreprocessor)
    assert adapter.system_id == "basa-default"
    assert adapter.version == "0.1.0"
    out = adapter.process("baperan")
    assert isinstance(out, str)


def test_basa_adapter_invalid_param_raises() -> None:
    with pytest.raises(RuntimeError, match="unsupported parameter"):
        BasaAdapter(
            system_id="basa-bad",
            params={"unsupported_kwarg": True},
        )


def test_sastrawi_adapter() -> None:
    adapter = SastrawiAdapter()
    assert isinstance(adapter, BasePreprocessor)
    assert adapter.system_id == "sastrawi"
    # Sastrawi stems 'berjalan' to 'jalan'
    out = adapter.process("berjalan")
    assert out == "jalan"
