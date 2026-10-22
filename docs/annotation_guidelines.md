# Annotation Guidelines — Pilot Dataset

Normative document for authoring and reviewing rows in `data/`. If a row contradicts this
document, the row is wrong.

Version: applies to `dataset_version = v1.0.0`.

---

## 1. What counts as normalization

Normalization converts informal Indonesian text into a **standard lexical and orthographic
form** while preserving meaning, register-neutral pronouns aside, and the identity of every
name, entity and technical term.

`raw_input` and `expected_output` must differ only by the transformations defined in §2. Nothing
else may change: no paraphrasing, no definition glossing, no added or removed information, no
punctuation "tidying" beyond what the transformation itself requires, no translation of English
jargon, no register shift beyond the pinned pronoun table.

### 1.1 Banned transformations

| Banned | Example | Why |
|---|---|---|
| Definition glossing | `baperan → mudah terbawa perasaan` | A glossary entry, not a normalization. The result is a definition, not the same utterance. |
| Paraphrase | `otw skrg → dalam perjalanan sekarang` | Free translation with invented syntax. |
| Normalizing a valid KBBI word | `ketiak → ketika` | `ketiak` means "armpit". Nothing is wrong with it. Producing this pair in gold teaches a normalizer to corrupt a real word. |
| Translating clean English jargon | `deploy → meluncurkan` | Violates the preservation policy (§4). |
| Register inflation | `mager → malas` is acceptable only as `mager → malas gerak` | `malas` is a partial, meaning-changing truncation. |
| Emoji or punctuation "cleanup" | `🙂` removed, `...` → `.` | Out of scope; metrics do not score it, and gold must not encode it. |

---

## 2. Slice classification by derivability

A row belongs to the slice whose single transformation reproduces `expected_output` from
`raw_input`. Classify by **applying the operation**, never by how the text looks.

```
op(raw) == expected_output ?
  repetition_collapse : collapse every character run of length >= 3 to one character
  vowel_expansion     : restore omitted vowels in an abbreviation
  lexicon_lookup      : one dictionary hop from a colloquial form to its standard form
  character_edit      : one insertion, deletion or substitution yielding a non-word
  identity            : raw == expected
```

| Result | Slice | `applied_ops` |
|---|---|---|
| Only `repetition_collapse` | `repetition_reduction` | `["repetition_collapse"]` |
| Only `vowel_expansion` | `abbreviation_phonetic` | `["vowel_expansion"]` |
| Only `lexicon_lookup` | `slang_lexical` | `["lexicon_lookup"]` |
| Only `character_edit` | `typo_nonword` | `["character_edit"]` |
| Identity | negative control | `[]` |
| Two or more operations | `mixed_challenge` | ordered list |
| No single operation reproduces gold | **reject the row** | — |

### 2.1 Worked classifications

| Row | Verdict |
|---|---|
| `iyaaaaa → iya` | `repetition_reduction`. Collapsing the run gives gold. |
| `bisaaa → bisa` | `repetition_reduction`. |
| `gkkkk → tidak` | **Not** `repetition_reduction`. Collapse gives `gk`, which still needs a lookup. If you want this row, the operation set is `["repetition_collapse", "lexicon_lookup"]`, so it belongs in `mixed_challenge`. |
| `bngtttt → banget` | Same: collapse yields `bngtt`, which is not `banget`. Mixed. |
| `blm → belum` | `abbreviation_phonetic`. |
| `sdh → sudah` | `abbreviation_phonetic`. |
| `mager → malas gerak` | `slang_lexical`. One dictionary hop. |
| `tehknik → teknik` | `typo_nonword`. One transposition of adjacent characters, result is a non-word. |
| `ktika → ketika` | `typo_nonword`. One deletion, result is a non-word. Note `ketiak` is a different word and is not a target. |
| `Google → google` | Not a row. Case is out of scope; a row whose only difference is case has no eligible operation and must be rejected. |

### 2.2 The hardest rule

If you cannot name the operation, the row does not exist. "It just looks more standard" is not
a classification.

---

## 3. Slices

### 3.1 `repetition_reduction` (30 rows)

Standard-word text with elongated runs. Exactly one collapse produces gold.

- Valid: `iyaaaaa → iya`, `bisaaa → bisa`, `tidaaaak → tidak`, `apaaa → apa`.
- Invalid: anything whose collapse still leaves a colloquial form (`gkkkk`, `bngtttt`, `dapettt`).
- Authoring constraint: 30 rows of genuine standard-word elongation is hard. Do not pad with
  colloquial bases; if a candidate's base form is not standard, it belongs in `slang_lexical` or
  `mixed_challenge`.

### 3.2 `slang_lexical` (30 rows)

A single dictionary hop from a colloquial form to a standard form.

- Valid: `mager → malas gerak`, `gabut → tidak ada pekerjaan`, `bohay → bodoh`.
- The gold must be the accepted expansion, not an explanation. Two words are fine; a clause is
  a gloss and is banned.
- Multi-word slang where the expansion is idiomatic (`mager`) is allowed; the test is that a
  dictionary maps one string to the other.

### 3.3 `abbreviation_phonetic` (30 rows)

Vowel omission and consonant skeletons, restored.

- Valid: `blm → belum`, `sdh → sudah`, `dgn → dengan`, `utk → untuk`, `krn → karena`.
- Invalid: consonant reduction that is really a different lexical item (`gk`, `gak`, `nggak`
  are colloquial words, not abbreviations of `tidak`) — those are `slang_lexical`.

### 3.4 `typo_nonword` (30 rows)

Exactly one character-level edit producing a token that is **not a word in KBBI**.

- Valid: `tehknik → teknik`, `ktika → ketika`, `memebuat → membuat`.
- Invalid: real words (`ketiak`), double edits, and edits that produce another real word
  (`bisa → bisa` no-op; `makan → makam` is a word, so it is not a non-word typo).

### 3.5 `negative_controls_kbbi` (30 rows)

Formal prose that a normalizer must not touch. `raw_input == expected_output`,
`negative_control: true`, `applied_ops: []`.

Must contain at least 40 protected entities across this slice and §3.6 combined, with a mix of:

- brand and product names with internal capitals (`Gojek`, `Shopee`, `Tokopedia`);
- technical terms (`Kubernetes`, `Kafka`, `PostgreSQL`, `deploy`, `staging`);
- URLs including one with a path and one with a trailing sentence period;
- file names and versions (`node.js`, `v1.2.3`, `app.py`);
- numbers with separators (`Rp 1.000.000`, `3,14`, `2024`).

### 3.6 `negative_controls_code_switching` (30 rows)

Indonesian sentences carrying English IT vocabulary that must survive verbatim. Also
`negative_control: true` — so `raw_input == expected_output` — which means **no slang and no
abbreviations** may appear in these rows. A sentence that needs both preservation and
normalization belongs in `mixed_challenge`.

### 3.7 `mixed_challenge` (30 rows, exploratory, ungated)

Two or more operations in one sentence, e.g. `iyaaaaa mksd lu apa sih, nanti gue meeting sama
tim Kafka` → `iya maksud kamu apa sih, nanti saya meeting dengan tim Kafka`.

These rows exist to expose composed failures. They carry `applied_ops` for every operation and
are excluded from gate evaluation by construction.

---

## 4. Preservation policy

### 4.1 Pinned pronoun table

| Raw | Gold |
|---|---|
| `gw`, `gue`, `gua`, `w` | `saya` |
| `lu`, `loe`, `u` | `kamu` |

No alternatives. `aku` is not a gold target in this dataset; a SUT that emits `aku` is scored as
wrong, and that is a deliberate, documented choice, not an oversight.

### 4.2 English jargon

Preserved verbatim, including capitalisation in `raw_input` (case is out of the comparison, but
gold must be written as the text appears):

`deploy`, `staging`, `production`, `sprint`, `backlog`, `meeting`, `sync`, `deadline`, `scope`,
`rollback`, `commit`, `branch`, `merge`, `Kubernetes`, `Kafka`, `PostgreSQL`, `Redis`, `node.js`,
`Docker`, `CI/CD`.

An English word is translated only when the raw text already mixes forms inconsistently, and
then it is recorded as a `lexicon_lookup` with a reference to this section. When in doubt,
preserve.

### 4.3 Protected entities

Every `metadata.protected_entities` entry must appear verbatim (case-insensitively) in
`raw_input`. The schema validator rejects rows that violate this, because an entity that is not
present cannot be preserved and would inflate the preservation denominator.

---

## 5. Authoring workflow

1. Author in batches of 10 rows per slice.
2. Run `basa-eval validate-dataset --slice <name>` after every batch. It checks: schema, unique
   ids, slice ⇔ filename agreement, `applied_ops` agreement with §2, negative-control
   equivalence, entity presence, duplicate `raw_input` across slices.
3. Second pass: read every row as if you were the normalizer and ask "would I have produced
   exactly this?" Any hesitation means the row is ambiguous and must be rewritten or dropped.
4. Third pass, locked: a row may only be changed under §6.

### 5.1 Rejection checklist

Drop the row if any is true:

- gold requires more than the operations you declared;
- gold changes meaning, adds information, or removes information;
- gold translates jargon;
- gold aligns with BASA's known output rather than with the standard form (authoring to the
  incumbent is data leakage);
- the same `raw_input` appears in another slice;
- the row's difficulty field would be hard to defend (`easy/medium/hard` is about how far the
  raw text is from standard, not about how long the sentence is).

---

## 6. Amendment policy

| Kind | Version | Requirements |
|---|---|---|
| Mechanical: malformed JSON line, schema violation, duplicate id, trailing whitespace, `dataset_version` mismatch | patch, e.g. `v1.0.1` | fix + changelog line naming the commit |
| Semantic: any change to `raw_input`, `expected_output`, `negative_control`, `applied_ops`, slice membership | minor, e.g. `v1.1.0` | one line per row in `docs/findings/gold-changelog.md`: `row id \| old \| new \| rationale`, and all earlier runs against the previous version are marked stale |

**Editing gold so that a gate turns green is a prohibited change** unless it is recorded as a
semantic amendment with a rationale that stands on its own — the rationale must make sense to
someone who has never seen the failing run. "BASA's output looked reasonable" is not a
rationale; it is the failure mode this dataset exists to detect.
