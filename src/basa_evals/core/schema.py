"""Core Pydantic data contracts, validation rules, and schema definitions."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

NormalizationOp = Literal[
    "repetition_collapse",
    "vowel_expansion",
    "lexicon_lookup",
    "character_edit",
]

SINGLE_OP_SLICES = {
    "repetition_reduction": "repetition_collapse",
    "slang_lexical": "lexicon_lookup",
    "abbreviation_phonetic": "vowel_expansion",
    "typo_nonword": "character_edit",
}


class SampleMetadata(BaseModel):
    """Metadata attached to an evaluation sample."""

    protected_entities: list[str] = Field(default_factory=list)
    source: str = "curated_pilot_v2"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    extra: dict[str, Any] = Field(default_factory=dict)


class Sample(BaseModel):
    """A single evaluation benchmark item."""

    id: str = Field(..., description="Unique sample identifier (e.g. 'gold-slang-0001')")
    dataset_version: str = Field(..., description="Semantic dataset release version")
    slice: str = Field(..., description="Slice label matching file category")
    domain: str = Field(default="social_chat", description="Domain context")
    raw_input: str = Field(..., min_length=1, description="Raw input text")
    expected_output: str = Field(..., min_length=1, description="Canonical gold target")
    negative_control: bool = Field(
        default=False,
        description="True if expected_output must strictly equal raw_input",
    )
    applied_ops: list[NormalizationOp] = Field(default_factory=list)
    metadata: SampleMetadata = Field(default_factory=SampleMetadata)

    @model_validator(mode="after")
    def verify_sample_invariants(self) -> "Sample":
        # 1. Negative control invariants
        if self.negative_control:
            if self.raw_input != self.expected_output:
                raise ValueError(
                    f"Sample '{self.id}' is marked negative_control=True but raw_input "
                    f"must be identical to expected_output."
                )
            if self.applied_ops:
                raise ValueError(
                    f"Sample '{self.id}' is marked negative_control=True but applied_ops "
                    f"must be empty (found {self.applied_ops})."
                )
        else:
            if not self.applied_ops:
                raise ValueError(
                    f"Sample '{self.id}' is marked negative_control=False but applied_ops "
                    f"cannot be empty."
                )

        # 2. Slice taxonomy agreement
        if self.slice in SINGLE_OP_SLICES:
            if len(self.applied_ops) != 1:
                raise ValueError(
                    f"Slice '{self.slice}' requires exactly one applied operation in applied_ops, "
                    f"found {self.applied_ops}."
                )
            expected_op = SINGLE_OP_SLICES[self.slice]
            if self.applied_ops[0] != expected_op:
                raise ValueError(
                    f"Slice '{self.slice}' requires applied_op '{expected_op}', "
                    f"found '{self.applied_ops[0]}'."
                )
        elif self.slice == "mixed_challenge":
            if len(self.applied_ops) < 2:
                raise ValueError(
                    f"Slice 'mixed_challenge' requires at least 2 operations in applied_ops, "
                    f"found {len(self.applied_ops)}."
                )
        elif self.slice.startswith("negative_controls"):
            if not self.negative_control:
                raise ValueError(f"Slice '{self.slice}' must be marked negative_control=True.")

        # 3. Protected entities verification: must appear in raw_input
        raw_cf = self.raw_input.casefold()
        for entity in self.metadata.protected_entities:
            if entity.casefold() not in raw_cf:
                raise ValueError(
                    f"Sample '{self.id}' declares protected entity '{entity}' "
                    f"which is not present in raw_input '{self.raw_input}'."
                )

        return self


class Prediction(BaseModel):
    """Output produced by a System Under Test for a single sample."""

    sample_id: str
    system_id: str
    predicted_text: str


class MetricValue(BaseModel):
    """Calculated metric value with explicit numerator and denominator."""

    score: float | None = None
    numerator: float | None = None
    denominator: float | None = None
    sample_count: int = 0
    excluded_samples: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class SliceResult(BaseModel):
    """Evaluation metrics for a specific slice."""

    slice_name: str
    exploratory: bool
    sample_count: int
    metrics: dict[str, MetricValue]


class SystemResult(BaseModel):
    """Evaluation metrics for a system across all slices."""

    system_id: str
    system_version: str | None = None
    aggregate: dict[str, MetricValue]
    slices: dict[str, SliceResult]


class SliceGate(BaseModel):
    """Gate criteria for a single slice."""

    oner_max_errors: int | None = None
    uner_max_rate: float | None = None
    entity_preservation_min: float | None = None


class GateCriteria(BaseModel):
    """Suite-level gate configuration with scale rules."""

    oner_max_rate: float = 0.005
    oner_zero_tolerance_below: int = 500
    per_slice: dict[str, SliceGate] = Field(default_factory=dict)


class GateCheck(BaseModel):
    """Individual gate check outcome."""

    slice_name: str
    criterion: str
    threshold: float
    observed: float | None = None
    eligible: float | None = None
    passed: bool
    reason: str | None = None


class GateResult(BaseModel):
    """Overall gate verdict and individual check records."""

    passed: bool
    checks: list[GateCheck] = Field(default_factory=list)
    skipped_slices: list[str] = Field(default_factory=list)


class SliceConfig(BaseModel):
    """Configuration for a slice file within a suite."""

    path: str
    slice_name: str
    exploratory: bool = False


class SystemRunConfig(BaseModel):
    """Configuration for an evaluated SUT."""

    system_id: str
    adapter: str
    params: dict[str, Any] = Field(default_factory=dict)


class RunConfig(BaseModel):
    """Declarative specification for an evaluation run."""

    name: str
    description: str = ""
    tier: Literal["intrinsic"] = "intrinsic"
    dataset_version: str
    slices: list[SliceConfig]
    systems: list[SystemRunConfig]
    metrics: list[str] = Field(
        default_factory=lambda: [
            "exact_match",
            "exact_match_casefold",
            "cer",
            "wer",
            "oner",
            "uner",
            "entity_preservation",
        ]
    )
    gate: GateCriteria = Field(default_factory=GateCriteria)


class DatasetProvenance(BaseModel):
    """Cryptographic and row-count provenance for an evaluated slice."""

    path: str
    slice_name: str
    sha256: str
    rows: int


class SystemProvenance(BaseModel):
    """Provenance details for a system evaluated in a run."""

    system_id: str
    adapter: str
    version: str | None
    params: dict[str, Any]


class EvaluationReport(BaseModel):
    """Complete, reproducible evaluation run artifact."""

    run_id: str
    timestamp: str
    run_name: str
    evals_version: str
    python_version: str
    git_commit: str | None
    dataset_version: str
    datasets: list[DatasetProvenance]
    systems: list[SystemProvenance]
    results: list[SystemResult]
    gate: GateResult
    gate_mode: Literal["enforced", "advisory"] = "enforced"


class RunProvenance(BaseModel):
    """Runtime and environmental provenance details."""

    git_commit: str | None = None
    basa_evals_version: str = "0.1.0a0"
    python_version: str
    platform_system: str
    platform_machine: str


class SampleTokenizerResult(BaseModel):
    """Tokenizer statistics for a single sample under a specific preprocessor and tokenizer."""

    sample_id: str
    slice_name: str
    tokenizer_id: str
    raw_tokens: int
    pred_tokens: int
    gold_tokens: int
    raw_sfi: float
    pred_sfi: float
    compression_ratio: float = Field(
        ..., description="Raw tokens / max(1, pred tokens). >1.0 indicates savings."
    )
    token_delta: int = Field(
        ..., description="Raw tokens - pred tokens. Positive indicates reduction."
    )


class SliceTokenizerSummary(BaseModel):
    """Aggregate tokenization metrics for a specific slice."""

    slice_name: str
    tokenizer_id: str
    total_samples: int
    total_raw_tokens: int
    total_pred_tokens: int
    total_gold_tokens: int
    corpus_compression_ratio: float
    net_savings_rate: float
    mean_raw_sfi: float
    mean_pred_sfi: float
    delta_sfi: float
    compression_count: int = Field(..., description="Samples where token_delta > 0")
    inflation_count: int = Field(..., description="Samples where token_delta < 0")
    neutral_count: int = Field(..., description="Samples where token_delta == 0")


class SystemTokenizerSummary(BaseModel):
    """Aggregate tokenization metrics for a preprocessor system across a tokenizer."""

    system_id: str
    tokenizer_id: str
    total_raw_tokens: int
    total_pred_tokens: int
    corpus_compression_ratio: float
    net_savings_rate: float
    macro_compression_ratio: float
    mean_raw_sfi: float
    mean_pred_sfi: float
    mean_delta_sfi: float
    slice_breakdowns: dict[str, SliceTokenizerSummary]


class TokenizerBenchmarkReport(BaseModel):
    """Full cross-system, cross-tokenizer benchmark evaluation report."""

    run_id: str
    timestamp: str
    provenance: RunProvenance
    suite_name: str
    systems: list[str]
    tokenizers: list[str]
    results: list[SystemTokenizerSummary]
