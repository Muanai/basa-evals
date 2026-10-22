"""9-atom tokenizer with totality guarantees and comparison canonicalization."""

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class TokenKind(Enum):
    URL = "url"
    EMAIL = "email"
    TECH_ENTITY = "tech_entity"
    NUMERIC = "numeric"
    REDUP_HYPHEN = "redup_hyphen"
    REDUP_NUMERIC = "redup_numeric"
    WORD = "word"
    PUNCT = "punct"
    MISC = "misc"


@dataclass(frozen=True)
class Token:
    text: str
    kind: TokenKind
    char_span: tuple[int, int]


TOKEN_PATTERN = re.compile(
    r"(?P<URL>(?:https?://|www\.)(?:[^\s\"'<>.,;:!?()]|\([^\s\"'<>]*\)|[.,;:!?](?=[^\s\"'<>.,;:!?]))+)|"
    r"(?P<EMAIL>[\w.+-]+@[\w-]+(?:\.[\w-]+)+)|"
    r"(?P<TECH_ENTITY>[^\W\d_][\w-]*(?:\.[\w-]+)+)|"
    r"(?P<NUMERIC>\d+(?:[.,:/]\d+)*)|"
    r"(?P<REDUP_HYPHEN>[^\W\d_]+-[^\W\d_]+)|"
    r"(?P<REDUP_NUMERIC>[^\W\d_]+2\b)|"
    r"(?P<WORD>[^\W\d_]+(?:'[^\W\d_]+)?)|"
    r"(?P<PUNCT>[!\"#$%&'()*+,-./:;<=>?@\[\\\]^_`{|}~…“”‘’«»])|"
    r"(?P<MISC>.)"
)

ONER_ELIGIBLE_KINDS = {
    TokenKind.WORD,
    TokenKind.REDUP_HYPHEN,
    TokenKind.REDUP_NUMERIC,
    TokenKind.TECH_ENTITY,
    TokenKind.URL,
    TokenKind.EMAIL,
    TokenKind.NUMERIC,
}


def is_oner_eligible(token: Token) -> bool:
    """Check whether token is eligible for ONER/UNER metric calculations."""
    return token.kind in ONER_ELIGIBLE_KINDS


def tokenize(text: str) -> list[Token]:
    """Tokenize input text using 9 ordered atom rules, guaranteeing totality."""
    tokens: list[Token] = []
    # Strip whitespaces between tokens; tokens themselves capture non-whitespace characters
    for match in TOKEN_PATTERN.finditer(text):
        token_text = match.group()
        if token_text.isspace():
            continue
        kind_name = match.lastgroup
        assert kind_name is not None
        kind = TokenKind[kind_name]
        tokens.append(Token(text=token_text, kind=kind, char_span=match.span()))
    return tokens


def canonicalize(text: str, *, casefold: bool = False) -> str:
    """Apply comparison canonicalization rules R1-R6 to text."""
    # R1: NFC normalization
    result = unicodedata.normalize("NFC", text)

    # R2: Collapse internal whitespace runs to one space; strip ends
    result = re.sub(r"\s+", " ", result).strip()

    # R3: Optional casefold
    if casefold:
        result = result.casefold()

    # R4: Reduplication marker canonicalization (X-X -> XX; X2 -> XX)
    # Applied case-insensitively when words match
    result = re.sub(r"\b([^\W\d_]+)-\1\b", r"\1\1", result, flags=re.IGNORECASE)
    result = re.sub(r"\b([^\W\d_]+)2\b", r"\1\1", result, flags=re.IGNORECASE)

    # R5 & R6: Numeric separator removal (e.g. 1.000.000 -> 1000000, 3,14 -> 314)
    result = re.sub(r"(?<=\d)[.,](?=\d)", "", result)

    return result
