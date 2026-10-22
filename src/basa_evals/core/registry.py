"""Registry for resolving System Under Test adapters."""

from typing import Any, Callable
from basa_evals.adapters.base import BasePreprocessor
from basa_evals.adapters.basa import BasaAdapter
from basa_evals.adapters.identity import RawAdapter
from basa_evals.adapters.sastrawi import SastrawiAdapter
from basa_evals.adapters.simple_regex import SimpleRegexBaseline

_DEFAULT_REGISTRY: dict[str, Callable[..., BasePreprocessor]] = {
    "raw": RawAdapter,
    "simple_regex": SimpleRegexBaseline,
    "sastrawi": SastrawiAdapter,
    "basa": BasaAdapter,
}


class Registry:
    """Registry for discovering and instantiating SUT adapters."""

    _adapters: dict[str, Callable[..., BasePreprocessor]] = dict(_DEFAULT_REGISTRY)

    @classmethod
    def register(cls, key: str, factory: Callable[..., BasePreprocessor]) -> None:
        """Register a new adapter factory under key."""
        cls._adapters[key] = factory

    @classmethod
    def get(cls, adapter_key: str, **kwargs: Any) -> BasePreprocessor:
        """Resolve and instantiate an adapter by key."""
        if adapter_key not in cls._adapters:
            raise KeyError(
                f"Unknown adapter key '{adapter_key}'. Available keys: {sorted(cls._adapters.keys())}"
            )
        return cls._adapters[adapter_key](**kwargs)

    @classmethod
    def available_keys(cls) -> list[str]:
        """Return list of registered adapter keys."""
        return sorted(cls._adapters.keys())
