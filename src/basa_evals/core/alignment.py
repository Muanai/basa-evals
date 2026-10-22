"""Authoritative reference alignment and hypothesis projection enforcing conservation laws L1-L6."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from basa_evals.core.tokenizer import Token, canonicalize, is_oner_eligible


class SpanKind(Enum):
    CLEAN = "clean"
    NOISY = "noisy"


@dataclass
class ReferenceSpan:
    kind: SpanKind
    raw_tokens: list[Token]
    gold_tokens: list[Token]


@dataclass
class AlignmentResult:
    clean_tokens: int = 0
    noisy_tokens: int = 0
    preserved_clean: int = 0
    on_substitution_or_deletion: int = 0
    on_insertion: int = 0
    on_errors: int = 0
    correctly_fixed: int = 0
    un_errors: int = 0
    on_error_indices: set[int] = field(default_factory=set)
    un_error_indices: set[int] = field(default_factory=set)


def _wagner_fischer(
    seq1: list[str], seq2: list[str]
) -> list[tuple[Literal["M", "S", "D", "I"], int | None, int | None]]:
    """Compute token-level Levenshtein edit transcript between two string sequences.

    Returns list of (op, idx1, idx2) operations:
    - 'M': Match (seq1[idx1] == seq2[idx2])
    - 'S': Substitute (seq1[idx1] -> seq2[idx2])
    - 'D': Delete (seq1[idx1] deleted)
    - 'I': Insert (seq2[idx2] inserted)
    """
    n, m = len(seq1), len(seq2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],  # Substitute
                    dp[i - 1][j],      # Delete
                    dp[i][j - 1],      # Insert
                )

    # Backtrack to reconstruct alignment operations
    i, j = n, m
    ops: list[tuple[Literal["M", "S", "D", "I"], int | None, int | None]] = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and seq1[i - 1] == seq2[j - 1]:
            ops.append(("M", i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append(("S", i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(("D", i - 1, None))
            i -= 1
        else:
            ops.append(("I", None, j - 1))
            j -= 1

    ops.reverse()
    return ops


def align_reference(
    raw_tokens: list[Token], gold_tokens: list[Token]
) -> list[ReferenceSpan]:
    """Authoritatively partition raw tokens into CLEAN and NOISY reference spans."""
    raw_e = [t for t in raw_tokens if is_oner_eligible(t)]
    gold_e = [t for t in gold_tokens if is_oner_eligible(t)]

    c_raw = [canonicalize(t.text, casefold=True) for t in raw_e]
    c_gold = [canonicalize(t.text, casefold=True) for t in gold_e]

    ops = _wagner_fischer(c_raw, c_gold)

    spans: list[ReferenceSpan] = []
    current_kind: SpanKind | None = None
    curr_raw: list[Token] = []
    curr_gold: list[Token] = []

    for op, i, j in ops:
        kind = SpanKind.CLEAN if op == "M" else SpanKind.NOISY
        t_raw = [raw_e[i]] if i is not None else []
        t_gold = [gold_e[j]] if j is not None else []

        if current_kind is None:
            current_kind = kind
            curr_raw.extend(t_raw)
            curr_gold.extend(t_gold)
        elif current_kind == kind:
            curr_raw.extend(t_raw)
            curr_gold.extend(t_gold)
        else:
            spans.append(ReferenceSpan(kind=current_kind, raw_tokens=curr_raw, gold_tokens=curr_gold))
            current_kind = kind
            curr_raw = list(t_raw)
            curr_gold = list(t_gold)

    if current_kind is not None and (curr_raw or curr_gold):
        spans.append(ReferenceSpan(kind=current_kind, raw_tokens=curr_raw, gold_tokens=curr_gold))

    return spans


def project_hypothesis(
    reference_spans: list[ReferenceSpan], pred_tokens: list[Token]
) -> AlignmentResult:
    """Project hypothesis prediction onto authoritative reference spans, evaluating L1-L6."""
    pred_e = [t for t in pred_tokens if is_oner_eligible(t)]
    c_pred = [canonicalize(t.text, casefold=True) for t in pred_e]

    # Reconstruct canonicalized eligible gold sequence across all spans
    all_gold_e: list[Token] = []
    for span in reference_spans:
        all_gold_e.extend(span.gold_tokens)

    c_gold = [canonicalize(t.text, casefold=True) for t in all_gold_e]

    # Align gold_e to pred_e
    gold_pred_ops = _wagner_fischer(c_gold, c_pred)

    # Group operations by span
    res = AlignmentResult()
    gold_offset = 0

    for span in reference_spans:
        num_raw = len(span.raw_tokens)
        num_gold = len(span.gold_tokens)

        # Slice ops that belong to this span's gold interval: [gold_offset, gold_offset + num_gold)
        span_ops: list[tuple[Literal["M", "S", "D", "I"], int | None, int | None]] = []
        # Consume ops matching gold indices in range
        while gold_pred_ops:
            op, g_idx, p_idx = gold_pred_ops[0]
            if g_idx is not None:
                if g_idx < gold_offset + num_gold:
                    span_ops.append(gold_pred_ops.pop(0))
                else:
                    break
            else:
                # Insertion in pred (g_idx is None)
                # If we haven't consumed any gold tokens of next span, it belongs to current span
                span_ops.append(gold_pred_ops.pop(0))

        gold_offset += num_gold

        if span.kind == SpanKind.CLEAN:
            res.clean_tokens += num_raw
            # In a clean span: num_raw == num_gold
            clean_preserved = 0
            clean_sub_del = 0
            clean_ins = 0

            # Count matches, subs, and deletions
            for op, _g_idx, p_idx in span_ops:
                if op == "M":
                    clean_preserved += 1
                elif op in ("S", "D"):
                    clean_sub_del += 1
                    if p_idx is not None:
                        res.on_error_indices.add(p_idx)

            # Insertions strictly inside clean span
            # Boundary insertions are at span start or end; internal insertions are between matched tokens
            # Find first and last gold token indices in span_ops
            non_ins_ops = [op for op, g, p in span_ops if g is not None]
            if len(non_ins_ops) >= 2:
                # Count insertions that occur strictly between the first and last non-insertion operation
                first_idx = next(i for i, (op, g, p) in enumerate(span_ops) if g is not None)
                last_idx = len(span_ops) - 1 - next(i for i, (op, g, p) in enumerate(reversed(span_ops)) if g is not None)
                for k in range(first_idx + 1, last_idx):
                    op, g, p = span_ops[k]
                    if op == "I":
                        clean_ins += 1
                        if p is not None:
                            res.on_error_indices.add(p)

            res.preserved_clean += clean_preserved
            res.on_substitution_or_deletion += clean_sub_del
            res.on_insertion += clean_ins

        else:
            # NOISY span
            res.noisy_tokens += num_raw
            # Collect predicted tokens allocated to this noisy span
            pred_indices = [p for op, g, p in span_ops if p is not None]
            pred_span_c = [c_pred[p] for p in pred_indices]
            gold_span_c = [canonicalize(t.text, casefold=True) for t in span.gold_tokens]

            if pred_span_c == gold_span_c:
                res.correctly_fixed += num_raw
            else:
                res.un_errors += num_raw
                for p in pred_indices:
                    res.un_error_indices.add(p)

    res.on_errors = res.on_substitution_or_deletion + res.on_insertion
    return res
