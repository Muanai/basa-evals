# BASA Evals — Milestone 1 Baseline Evaluation Report

- **Date:** 2026-10-22
- **Suite:** `pilot_210` (Milestone 1 Intrinsic Suite)
- **Version:** `basa-evals 0.1.0a0`
- **Dataset Version:** `v1.0.0`
- **Gate Mode:** `enforced`
- **Gatekeeper Verdict:** **FAILED** (Candidate release gate not satisfied)

---

## 1. Executive Summary

Milestone 1 delivers the independent evaluation framework, benchmark suite, and dataset pipeline for Indonesian text preprocessing and normalization. The evaluation harness treats BASA and all baseline normalizers strictly as external Systems Under Test (SUTs) under the uniform `BasePreprocessor` protocol.

In this flagship baseline run, five systems were evaluated against the 210-sample `pilot_210` benchmark suite (60 negative controls, 120 single-phenomenon gold items, and 30 exploratory multi-phenomenon challenge items).

### Benchmark Leaderboard (Pilot-210)

| System | Version | EM exact | EM casefold | CER | WER | ONER | UNER | Entity Preservation | Status |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| `raw-identity` | *in-repo* | 28.6% | 28.6% | 0.0743 | 0.1802 | **0.0%** | 100.0% | **100.0%** | Baseline |
| `simple-regex` | `1.0.0` | 13.8% | 55.2% | 0.0632 | 0.2608 | **0.4%** | 64.7% | 95.5% | Baseline |
| `sastrawi` | `1.2.1` | 0.0% | 0.0% | 0.2443 | 0.6726 | **33.4%** | 100.0% | 79.1% | Stress Baseline |
| `basa-default` | `0.1.0` | 16.7% | 58.1% | 0.0709 | 0.2624 | **1.1%** | 52.6% | 95.5% | **FAILED** |
| `basa-full` | `0.1.0` | 16.7% | 58.1% | 0.0709 | 0.2624 | **1.1%** | 52.6% | 95.5% | **FAILED** |

> **Milestone 1 Success Criterion:** As mandated by Spec §1.3 and AGENTS.md, a **failing verdict on candidate normalizers is a successful milestone outcome**. The purpose of `basa-evals` is to expose destructive over-normalization errors before they corrupt downstream LLM and RAG pipelines. The harness has proven the existence of real, auditable defects.

---

## 2. Gatekeeper Evaluation Breakdown

For `basa-default` (and `basa-full`), the compound release gate evaluated all 6 non-exploratory slices against integer zero-tolerance thresholds ($N < 500$ clean tokens):

| Slice Name | Criterion | Threshold | Observed | Eligible Tokens | Verdict | Root Cause / Impact |
|---|:---:|---:|---:|---:|:---:|---|
| `negative_controls_kbbi` | `oner` | 0.0000 | **1.0000** | 190 | **FAIL** | 1 clean token corrupted (`www` mutated to `saya`) |
| `negative_controls_kbbi` | `entity_preservation` | 1.0000 | **0.9667** | 30 | **FAIL** | 1 protected entity destroyed (`www.indonesia.go.id`) |
| `negative_controls_code_switching` | `oner` | 0.0000 | **8.0000** | 213 | **FAIL** | 8 clean tokens corrupted (unprompted English translation + `lalu lintas`) |
| `negative_controls_code_switching` | `entity_preservation` | 1.0000 | **0.9459** | 37 | **FAIL** | 2 protected technical entities destroyed |
| `repetition_reduction` | `oner` | 0.0000 | **0.0000** | 1 | **PASS** | 0 clean tokens corrupted |
| `repetition_reduction` | `uner` | 0.1500 | **0.0333** | 30 | **PASS** | Run-collapse logic successfully resolved 29/30 items |
| `slang_lexical` | `oner` | 0.0000 | **0.0000** | 111 | **PASS** | 0 clean tokens corrupted |
| `slang_lexical` | `uner` | 0.1500 | **0.6000** | 30 | **FAIL** | Missing dictionary mappings for curated slang terms |
| `abbreviation_phonetic` | `oner` | 0.0000 | **0.0000** | 106 | **PASS** | 0 clean tokens corrupted |
| `abbreviation_phonetic` | `uner` | 0.1500 | **0.3667** | 30 | **FAIL** | Omitted vowel / consonant abbreviations left unexpanded |
| `typo_nonword` | `oner` | 0.0000 | **0.0000** | 91 | **PASS** | 0 clean tokens corrupted |
| `typo_nonword` | `uner` | 0.1500 | **1.0000** | 30 | **FAIL** | Typos untouched (`apply_typo: false` in default config) |

---

## 3. Deep Dive: Corrupted Tokens & Error Classification

Below is the complete audit of discrepancies produced by `basa-default` on clean negative controls, categorized under the normative guidelines:

### Finding 1: URL Domain Prefix Shredding
- **Sample ID:** `neg-kbbi-0026`
- **Raw Input:** `Portal resmi dapat diakses melalui www.indonesia.go.id.`
- **Gold Target:** `Portal resmi dapat diakses melalui www.indonesia.go.id.`
- **SUT Prediction:** `portal resmi dapat diakses melalui saya.indonesia.go.id.`
- **Classification:** `sut-bug`
- **Technical Analysis:** BASA's slang dictionary includes a rule mapping colloquial `w` $\rightarrow$ `saya`. Because the regex or tokenizer lacked domain-prefix boundary protection, `www` was mistakenly decomposed or matched as `w`, corrupting a valid web address into `saya.indonesia.go.id`. This directly fails both ONER ($1.0 > 0$) and Entity Preservation ($0.9667 < 1.0$).

### Finding 2: Collocation Mutation (`lalu lintas` $\rightarrow$ `kemudian lintas`)
- **Sample ID:** `neg-cs-0021`
- **Raw Input:** `Pengaturan load balancer mendistribusikan lalu lintas secara merata.`
- **Gold Target:** `Pengaturan load balancer mendistribusikan lalu lintas secara merata.`
- **SUT Prediction:** `pengaturan load balancer mendistribusikan kemudian lintas secara merata.`
- **Classification:** `sut-bug`
- **Technical Analysis:** BASA applies a context-free substitution of `lalu` ("then") $\rightarrow$ `kemudian`. In standard Indonesian, `lalu lintas` is an indivisible compound noun meaning "traffic". Mutating it to `kemudian lintas` destroys the semantic meaning of the sentence.

### Finding 3: Unprompted Translation of Preserved IT Jargon
- **Sample IDs:** `neg-cs-0004`, `neg-cs-0005`, `neg-cs-0014`, `neg-cs-0029`
- **Corrupted Items:**
  - `meeting` $\rightarrow$ `rapat` (`neg-cs-0004`)
  - `deadline` $\rightarrow$ `batas waktu` (`neg-cs-0005`)
  - `database` $\rightarrow$ `basis data` (`neg-cs-0014`, `neg-cs-0029`)
- **Classification:** `sut-bug`
- **Technical Analysis:** Under Annotation Guidelines §4.2, clean technical terms in engineering contexts must be preserved verbatim. A text normalizer is not a machine translator. Replacing technical loanwords with formal Indonesian translations causes vocabulary drift in code-switching environments.

---

## 4. Baseline Comparison & Ablation Analysis

- **`raw-identity` (No-Op Floor):** Provides mathematical validation of conservation laws. Passes ONER with 0 errors and 100% entity preservation, but fails UNER across all noisy slices with 100% error rate.
- **`sastrawi` (Destructive Stemmer Stress Baseline):** Achieved 33.4% ONER and 79.1% entity preservation. Proves that morphological stemmers cannot be substituted for text normalizers without devastating loss of grammatical affixes and named entities.
- **`simple-regex` (50-Entry Ablation Baseline):** Demonstrates that a naive 50-entry regex baseline achieves 55.2% casefold EM with only 0.4% ONER. BASA's incumbent margin over simple-regex is narrow (58.1% vs 55.2% EM), underscoring the necessity of expanding BASA's lexicon and fixing over-normalization.

---

## 5. Provenance & Reproducibility Statement

- **Run ID:** `e784108c-a716-42d4-b4b0-49db793d7734`
- **Git Commit:** `6848fac`
- **Python Version:** `3.12.6`
- **Suite Configuration:** `configs/suites/pilot_210.yaml`
- **Dataset Hashes (SHA-256):**
  - `negative_controls_kbbi`: `f910ba1b585efad6e9d6d376161476d05fca1c9a63901bcae5e1a17937402661`
  - `negative_controls_code_switching`: `c9bcf2793fa716e26cf81f96ba37b1ce8544e8ecdf01bf7b1348cbe886a11e86`
  - `repetition_reduction`: `bf4ae6e053912170ba26c9fca4ff366d925e01b7a2d64f0b2401f8d9518ccfd8`
  - `slang_lexical`: `5fe1c4ca9489f660ba2665b144bc34e366daec0914e66299042b474805e26715`
  - `abbreviation_phonetic`: `ff7480ee2e6ee54558e2254e0c46b97d192f592ba3c0762a4b8be56858e77ca8`
  - `typo_nonword`: `d475cfbc3d7d75ef9e68b3dc8617578ce2585fdb0186981cf1e133ca09f191cf`
  - `mixed_challenge`: `efef7aeaf2bb84fb74668db75bb5f514b8a1c97a829141be4031d2005085449d`
