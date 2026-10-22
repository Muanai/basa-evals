from basa_evals.core.tokenizer import (
    TokenKind,
    canonicalize,
    is_oner_eligible,
    tokenize,
)


def test_tokenizer_atom_precedence():
    cases = [
        ("https://gojek.com/karir.", "https://gojek.com/karir", TokenKind.URL),
        (
            "https://en.wikipedia.org/wiki/Foo_(bar)",
            "https://en.wikipedia.org/wiki/Foo_(bar)",
            TokenKind.URL,
        ),
        ("www.gojek.com/karir", "www.gojek.com/karir", TokenKind.URL),
        ("user@domain.com", "user@domain.com", TokenKind.EMAIL),
        ("node.js", "node.js", TokenKind.TECH_ENTITY),
        ("v1.2.3", "v1.2.3", TokenKind.TECH_ENTITY),
        ("Rp 1.000.000", "1.000.000", TokenKind.NUMERIC),
        ("3,14", "3,14", TokenKind.NUMERIC),
        ("10:30", "10:30", TokenKind.NUMERIC),
        ("kata-kata", "kata-kata", TokenKind.REDUP_HYPHEN),
        ("kata2", "kata2", TokenKind.REDUP_NUMERIC),
        ("café", "café", TokenKind.WORD),
        ("teknik", "teknik", TokenKind.WORD),
        ("!", "!", TokenKind.PUNCT),
        ("🙂", "🙂", TokenKind.MISC),
        ("€", "€", TokenKind.MISC),
    ]
    for text, expected_match, expected_kind in cases:
        tokens = tokenize(text)
        token_texts = [t.text for t in tokens]
        assert expected_match in token_texts, f"Expected {expected_match} in {token_texts}"
        t = next(tok for tok in tokens if tok.text == expected_match)
        assert t.kind == expected_kind, f"Token {expected_match} had kind {t.kind}, expected {expected_kind}"

def test_tokenizer_totality_guarantee():
    texts = [
        "Deploy ke node.js di https://gojek.com/karir untuk 3,14 café 🙂!",
        "Kunjungi www.tokopedia.com/promo, lalu email dev@tokopedia.com.",
        "Anak-anak berlari-lari bersama teman2 di kafe; biaya Rp 50.000 (diskon 10%).",
    ]
    for text in texts:
        tokens = tokenize(text)
        reconstructed = "".join(t.text for t in tokens)
        # All non-whitespace characters must be completely preserved in order
        assert "".join(text.split()) == "".join(reconstructed.split())

def test_oner_eligibility():
    tokens = tokenize("deploy ke Kafka v2.0 di https://gojek.com/karir!")
    eligible = [t.text for t in tokens if is_oner_eligible(t)]
    assert eligible == ["deploy", "ke", "Kafka", "v2.0", "di", "https://gojek.com/karir"]
    ineligible = [t.text for t in tokens if not is_oner_eligible(t)]
    assert ineligible == ["!"]

def test_canonicalize():
    assert canonicalize("Kata-Kata", casefold=True) == "katakata"
    assert canonicalize("kata2", casefold=True) == "katakata"
    assert canonicalize("1.000.000", casefold=True) == "1000000"
    assert canonicalize("3,14", casefold=True) == "314"
    assert canonicalize("  Halo   Dunia  ", casefold=False) == "Halo Dunia"
