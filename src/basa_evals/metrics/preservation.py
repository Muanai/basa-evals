"""Protected entity preservation evaluator."""

from basa_evals.core.tokenizer import canonicalize, tokenize


def check_entity_preservation(pred: str, protected_entities: list[str]) -> tuple[int, int]:
    """Check how many protected entities are preserved as contiguous subsequences.

    An entity is preserved when its case-folded canonicalized token sequence appears
    as a contiguous subsequence of the prediction's canonicalized token list.
    """
    if not protected_entities:
        return 0, 0

    pred_tokens = [canonicalize(t.text, casefold=True) for t in tokenize(pred)]
    preserved = 0

    for entity in protected_entities:
        ent_tokens = [canonicalize(t.text, casefold=True) for t in tokenize(entity)]
        if not ent_tokens:
            continue
        ent_len = len(ent_tokens)
        found = False
        for i in range(len(pred_tokens) - ent_len + 1):
            if pred_tokens[i : i + ent_len] == ent_tokens:
                found = True
                break
        if found:
            preserved += 1

    return preserved, len(protected_entities)
