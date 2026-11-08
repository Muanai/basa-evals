# BASA Evals (`basa-evals`)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data License: CC-BY-4.0](https://img.shields.io/badge/Data%20License-CC--BY--4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**BASA Evals** is an independent, neutral evaluation framework, benchmark suite, and dataset pipeline designed to systematically measure text normalization and preprocessing for Indonesian NLP (standard Indonesian, Bahasa Gaul slang, character repetition, non-word typos, and code-switching).

It treats every normalizer — including BASA — as an external **System Under Test (SUT)** behind a uniform protocol (`BasePreprocessor`), and measures normalization quality across three rigorous evaluation tiers: **Intrinsic Linguistic Fidelity**, **Multi-Tokenizer Efficiency**, and **Applied Downstream Task Impact**.

---

## 1. Core Mission & Philosophy

The framework answers one question without favour: **does a given normalizer improve informal Indonesian text without destroying clean text or hurting downstream models?**

- **Preservation First:** Under-normalization (slang left untouched) costs tokenizer efficiency. Over-normalization (clean KBBI text, brand names, technical terms, and code-switched jargon mutated into something else) corrupts meaning silently upstream of LLM and RAG pipelines.
- **Mandatory Negative Controls:** Every intrinsic benchmark suite must contain at least **20% negative-control samples** (`raw_input == expected_output`).
- **Strict Release Gatekeeper:** Candidate releases must achieve $\text{ONER} = 0$ (zero errors) on pilot slices ($N < 500$ clean tokens) and $\text{ONER} < 0.5\%$ on scaled benchmark suites.
- **Three-Tier Evaluation:** Normalization is evaluated intrinsically (edit distance & preservation), structurally (subword tokenizer fragmentation), and operationally (classification accuracy and $F_1$ deltas).

---

## 2. Three-Tier Benchmark Suites

### Tier 1: Intrinsic Linguistic Precision (`pilot_210`)
Measures exact transformation correctness and negative-control preservation across 210 curated rows:

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

### Tier 2: Multi-Tokenizer Efficiency (`tokenizer_pilot`)
Measures whether normalization reduces prompt token counts and mitigates context fragmentation across leading foundation models:
- **Evaluated Tokenizers:** OpenAI GPT-4o (`o200k_base`), Meta LLaMA-3 (BPE 128k), IndoBERT (WordPiece 32k), Gemma-2 (SentencePiece), and lightweight offline mock subword tokenizers.

### Tier 3: Applied Downstream Tasks (`downstream_smsa`)
Measures downstream task accuracy deltas on real-world Indonesian customer review sentiment:
- **Corpus:** 150 balanced IndoNLU SmSA test samples (50 positive, 50 neutral, 50 negative).
- **Classifiers:** Built-in offline `MockSentimentClassifier` (zero external dependencies) and fine-tuned `HuggingFaceSentimentClassifier` (`wirasana/indobert-sentiment-smsa`).

---

## 3. Metrics Formulation

### Intrinsic Metrics (Tier 1)
- **Exact Match (Dual Metric):**
  - `EM_exact`: String equality after NFC normalization and whitespace stripping.
  - `EM_casefold`: Case-insensitive exact match after NFC normalization.
- **Character Error Rate (CER):** $\sum \text{Lev}_{\text{chars}}(\text{pred}, \text{gold}) / \sum \max(1, \text{len}(\text{gold}))$.
- **Word Error Rate (WER):** $\sum \text{Lev}_{\text{words}}(\text{pred}, \text{gold}) / \sum \max(1, |\text{gold word tokens}|)$.
- **Over-Normalization Error Rate (ONER):** $\sum \text{ON Errors} / \sum \text{Clean Tokens}$.
- **Under-Normalization Error Rate (UNER):** $\sum \text{UN Errors} / \sum \text{Noisy Tokens}$.
- **Entity Preservation Rate:** $\sum \text{Entities Preserved} / \sum \text{Entities Expected}$.

### Tokenizer Efficiency Metrics (Tier 2)
- **Token Compression Ratio:** $\text{Raw Tokens} / \max(1, \text{Pred Tokens})$.
- **Net Savings Rate:** $(\text{Raw Tokens} - \text{Pred Tokens}) / \text{Raw Tokens}$.
- **Subword Fragmentation Index (SFI):** Average subwords per whitespace-delimited word ($\text{SFI} = T / W$). Lower SFI indicates reduced fragmentation.

### Downstream Task Metrics (Tier 3)
- **Accuracy & Macro $F_1$ Deltas:** $\Delta\text{Acc} = \text{Acc}_{\text{norm}} - \text{Acc}_{\text{raw}}$, $\Delta F_1 = F_{1,\text{norm}} - F_{1,\text{raw}}$.
- **Sample Outcome Partitioning:** Every sample is partitioned into **Win**, **Loss**, or **Neutral** under normalization:
  - $\text{Win}$: Raw incorrect, normalized correct.
  - $\text{Loss}$: Raw correct, normalized incorrect.
  - $\text{Neutral}$: Both correct or both incorrect.
- **Net Win Rate:** $(\text{Wins} - \text{Losses}) / N_{\text{total}}$.
- **Conservation Invariant:** $\text{Wins} + \text{Losses} + \text{Neutrals} = N_{\text{total}}$ holds strictly across all systems, with zero delta on `raw-identity`.

---

## 4. Quickstart & Installation

```bash
# Basic installation (pure Python, zero heavy dependencies)
pip install basa-evals

# With subword tokenizers (tiktoken, transformers)
pip install "basa-evals[tokenizers]"

# With downstream transformer classifiers (torch, transformers)
pip install "basa-evals[downstream]"

# Full installation including SUT baselines (basa, PySastrawi)
pip install "basa-evals[basa,sastrawi,tokenizers,downstream,dev]"
```

### CLI Commands

#### Tier 1: Intrinsic Linguistic Evaluation
```bash
# Run the pilot suite across all registered systems
basa-eval run --suite pilot_210

# Run evaluation on a specific system
basa-eval run --suite pilot_210 --system basa-default

# Run in advisory mode (record results without failing on gate exit code)
basa-eval run --suite pilot_210 --no-gate
```

#### Tier 2: Multi-Tokenizer Efficiency Benchmark
```bash
# Run tokenizer benchmark across GPT-4o and LLaMA-3
basa-eval tokenize --suite tokenizer_pilot --tokenizers gpt-4o,llama-3

# Run with offline mock tokenizer (zero dependencies)
basa-eval tokenize --suite tokenizer_pilot --tokenizers mock-subword
```

#### Tier 3: Applied Downstream Task Benchmark
```bash
# Run sentiment classification benchmark on IndoNLU SmSA test split
basa-eval downstream --suite downstream_smsa --classifier mock-sentiment

# Export JSON and Markdown benchmark reports
basa-eval downstream --suite downstream_smsa --classifier mock-sentiment --output-dir reports/
```

#### Discovery & Inspection Utilities
```bash
# List available suites, systems, tokenizers, and classifiers
basa-eval list-suites
basa-eval list-systems
basa-eval list-tokenizers
basa-eval list-classifiers

# Validate dataset integrity across all slices
basa-eval validate-dataset
```

---

## 5. Explicit Non-Goals & Known Limitations

| Limitation | Statement |
|---|---|
| **Single-phenomenon scope** | In Tier 1, the six gated slices each target one isolated phenomenon. Multi-phenomenon interactions are measured in the exploratory `mixed_challenge` slice. |
| **Case invariance** | ONER and entity preservation compare case-folded tokens. Legitimate capitalization changes are monitored via the `EM exact` diagnostic column. |
| **Punctuation invariance** | Punctuation tokens are ineligible for ONER. Punctuation edits appear in CER/WER only and do not fail the preservation gate. |
| **Statistical inference** | Benchmark slices in the pilot are curated at 30 rows per phenomenon (150 rows in SmSA). Differences below ~10 percentage points on small slices should be interpreted directionally. |

---

## 6. License & Data Governance

- **Software Code:** [MIT License](LICENSE)
- **Evaluation Slices:** [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)
- All benchmark slices are manually curated or synthetically constructed under explicit provenance. No raw, unconsented social media scrapes are used.
