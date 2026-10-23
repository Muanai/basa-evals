from datetime import timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from basa_evals.core.alignment import align_reference, project_hypothesis
from basa_evals.core.tokenizer import is_oner_eligible, tokenize


def test_closed_form_insertion_counters() -> None:
    raw = tokenize("Aplikasi Kafka berjalan")
    gold = tokenize("Aplikasi Kafka berjalan")
    pred = tokenize("Aplikasi Kafka yang berjalan")

    ref_spans = align_reference(raw, gold)
    res = project_hypothesis(ref_spans, pred)

    assert res.clean_tokens == 3
    assert res.preserved_clean == 3
    assert res.on_substitution_or_deletion == 0
    assert res.on_insertion == 1
    assert res.on_errors == res.on_substitution_or_deletion + res.on_insertion
    # Conservation law L1 must hold exactly
    assert res.preserved_clean + res.on_substitution_or_deletion == res.clean_tokens


def test_boundary_conditions() -> None:
    raw = tokenize("gw bgt")
    gold = tokenize("saya sangat")
    ref_spans = align_reference(raw, gold)

    # When pred == gold: 0 ON, 0 UN
    res_gold = project_hypothesis(ref_spans, gold)
    assert res_gold.on_errors == 0
    assert res_gold.un_errors == 0

    # When pred == raw: 0 ON, UN == noisy_tokens
    res_raw = project_hypothesis(ref_spans, raw)
    assert res_raw.on_errors == 0
    assert res_raw.un_errors == res_raw.noisy_tokens


@settings(max_examples=100, deadline=timedelta(milliseconds=500))
@given(
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        min_size=1,
        max_size=40,
    ),
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        min_size=1,
        max_size=40,
    ),
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        min_size=1,
        max_size=40,
    ),
)
def test_hypothesis_conservation_laws(r: str, g: str, p: str) -> None:
    raw = tokenize(r)
    gold = tokenize(g)
    pred = tokenize(p)
    raw_eligible = [t for t in raw if is_oner_eligible(t)]
    if not raw_eligible:
        return

    ref_spans = align_reference(raw, gold)
    res = project_hypothesis(ref_spans, pred)

    # Conservation Laws L1, L2, L6
    assert res.preserved_clean + res.on_substitution_or_deletion == res.clean_tokens
    assert res.correctly_fixed + res.un_errors == res.noisy_tokens
    assert res.clean_tokens + res.noisy_tokens == len(raw_eligible)
