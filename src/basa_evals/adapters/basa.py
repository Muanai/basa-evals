"""BASA preprocessor adapter with construction-time signature checks."""

import inspect
from typing import Any


class BasaAdapter:
    """Adapter for the BASA normalization library."""

    def __init__(
        self,
        system_id: str = "basa-default",
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._system_id = system_id
        self._params = dict(params or {})

        try:
            import basa

            self._basa = basa
        except ImportError as e:
            raise ImportError(
                "basa is required for BasaAdapter. "
                "Install via `pip install basa-evals[basa]` or install basa."
            ) from e

        # Validate params against basa.normalize signature
        sig = inspect.signature(basa.normalize)
        valid_params = set(sig.parameters.keys()) - {"text"}
        for k in self._params:
            if k not in valid_params:
                raise RuntimeError(
                    f"basa.normalize received unsupported parameter '{k}'. "
                    f"Supported parameters are: {sorted(valid_params)}"
                )

    @property
    def system_id(self) -> str:
        return self._system_id

    @property
    def version(self) -> str | None:
        return getattr(self._basa, "__version__", None)

    @property
    def params(self) -> dict[str, Any]:
        return self._params

    def process(self, text: str) -> str:
        res = self._basa.normalize(text, **self._params)
        if isinstance(res, list):
            return res[0] if res else ""
        return res

    def process_batch(self, texts: list[str]) -> list[str]:
        res = self._basa.normalize(texts, **self._params)
        if isinstance(res, str):
            return [res]
        return list(res)
