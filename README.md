# BASA Evals (`basa-evals`)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data License: CC-BY-4.0](https://img.shields.io/badge/Data%20License-CC--BY--4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**BASA Evals** is an independent, neutral evaluation framework, benchmark suite, and dataset pipeline designed to systematically measure text normalization and preprocessing for Indonesian NLP (standard Indonesian, Bahasa Gaul slang, character repetition, non-word typos, and code-switching).

It treats every normalizer — including BASA — as an external **System Under Test (SUT)** behind a uniform protocol (`BasePreprocessor`), and measures intrinsic normalization quality with auditable, mathematically verified metrics.

---

## 1. Core Mission & Philosophy

The framework answers one question without favour: **does a given normalizer improve informal Indonesian text without destroying clean text?**

- **Preservation First:** Under-normalization (slang left untouched) costs tokenizer efficiency. Over-normalization (clean KBBI text, brand names, technical terms, and code-switched jargon mutated into something else) corrupts meaning silently upstream of LLM and RAG pipelines.
- **Mandatory Negative Controls:** Every benchmark slice suite must contain at least **20% negative-control samples** (`raw_input == expected_output`).
- **Strict Release Gatekeeper:** Candidate releases must achieve $\text{ONER} = 0$ (zero errors) on pilot slices ($N < 500$ clean tokens) and $\text{ONER} < 0.5\%$ on scaled benchmark suites.
- **Independent SUT Architecture:** BASA and all competing baselines (`raw-identity`, `simple-regex`, `sastrawi`) compete symmetrically via the `BasePreprocessor` protocol.

---

## 2. Benchmark Suites (Pilot-210)

The Milestone 1 benchmark suite (`pilot_210`) contains **210 curated rows** across 7 slices:

| Slice | Rows | Category | Target Phenomenon | Gate Criteria |
|---|---:|---|---|---|
| `negative_controls_kbbi` | 30 | Negative Control | Formal Indonesian, URLs, numbers, entities | $\text{ONER} = 0$, $\text{Entity} = 100\%$ |
| `negative_controls_code_switching` | 30 | Negative Control | Indonesian with preserved English IT terms | $\text{ONER} = 0$, $\text{Entity} = 100\%$ |
| `repetition_reduction` | 30 | Gold Slice | Character runs $\ge 3$ on standard words | $\text{ONER} = 0$, $\text{UNER} \le 15\%$ |
| `slang_lexical` | 30 | Gold Slice | Colloquial slang dictionary mapping | $\text{ONER} = 0$, $\text{UNER} \le 15\%$ |
| `abbreviation_phonetic` | 30 | Gold Slice | Consonant skeletons and omitted vowels | $\text{ONER} = 0$, $\text{UNER} \le 15\%$ |
| `typo_nonword` | 30 | Gold Slice | Single-edit non-word typos | $\text{ONER} = 0$, $\text{UNER} \le 15\%$ |
| `mixed_challenge` | 30 | Exploratory | Composed phenomena ($\ge 2$ operations) | *Ungated diagnostics* |

Negative control ratio: **60 / 180 = 33.3%** of the gated population, **60 / 210 = 28.6%** of the total.

---

## 3. Metrics

All corpus-level metrics are computed as ratio-of-sums over eligible tokens:

- **Exact Match (Dual Metric):**
  - `EM_exact`: String equality after NFC normalization and whitespace stripping.
  - `EM_casefold`: Case-insensitive exact match after NFC normalization.
- **Character Error Rate (CER):** $\sum \text{Lev}_{\text{chars}}(\text{pred}, \text{gold}) / \sum \max(1, \text{len}(\text{gold}))$.
- **Word Error Rate (WER):** $\sum \text{Lev}_{\text{words}}(\text{pred}, \text{gold}) / \sum \max(1, |\text{gold word tokens}|)$.
- **Over-Normalization Error Rate (ONER):** $\sum \text{on\_errors} / \sum \text{clean\_tokens}$.
- **Under-Normalization Error Rate (UNER):** $\sum \text{un\_errors} / \sum \text{noisy\_tokens}$.
- **Entity Preservation Rate:** $\sum \text{entities\_preserved} / \sum \text{entities\_expected}$.

---

## 4. Quickstart & Installation

```bash
# Clone the repository
git clone https://github.com/Muanai/basa-evals.git
cd basa-evals

# Install in editable mode
pip install -e .

# Install optional dependencies for BASA and Sastrawi adapters
pip install -e ".[basa,sastrawi,dev]"
```

### CLI Commands

```bash
# Run the pilot suite across all registered systems
basa-eval run --suite pilot_210

# Run evaluation on a specific system
basa-eval run --suite pilot_210 --system basa-default

# Run in advisory mode (record results without failing on gate exit code)
basa-eval run --suite pilot_210 --no-gate

# List available suites and SUT adapters
basa-eval list-suites
basa-eval list-systems

# Validate dataset integrity across all slices
basa-eval validate-dataset

# Inspect a generated JSON run artifact
basa-eval inspect runs/<run_id>.json
```

---

## 5. Explicit Non-Goals & Known Limitations

| Limitation | Statement |
|---|---|
| **Single-phenomenon scope** | The six gated slices each require exactly one transformation. Composed multi-stage behaviour on mixed sentences is measured only by the ungated exploratory slice and is **not** claimed by any gate. |
| **Case invariance** | ONER and entity preservation compare case-folded tokens. A SUT that flattens legitimate capitalization is invisible to the preservation gate; case fidelity is visible only through the `EM exact` diagnostic column. |
| **Punctuation invariance** | Punctuation tokens are ineligible for ONER. Punctuation edits appear in CER/WER only and cannot fail the preservation gate. |
| **No latency or throughput** | Milestone 1 is `tier: intrinsic` only. Latency, throughput, and downstream-task tiers are out of scope for M1. |
| **No statistical inference** | Slice sizes are 30 rows. Differences below ~13 percentage points on a 30-row slice are indistinguishable from sampling noise. All M1 leaderboards are directional. |
| **Coverage of non-Latin scripts** | A whole non-Latin run (e.g. CJK) becomes one `WORD` token. Emoji and symbols become `MISC` tokens, counted but not analysed. |

---

## 6. License & Data Governance

- **Software Code:** [MIT License](LICENSE)
- **Evaluation Slices:** [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)
- All benchmark slices are manually curated or synthetically constructed under explicit provenance. No raw, unconsented social media scrapes are used.
