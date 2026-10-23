import pytest
from basa_evals.tokenizers.base import TokenizerAdapter
from basa_evals.tokenizers.mock import MockTokenizerAdapter
from basa_evals.tokenizers.registry import TokenizerRegistry


def test_mock_tokenizer_contract_and_behavior():
    tok = MockTokenizerAdapter()
    assert isinstance(tok, TokenizerAdapter)
    assert tok.tokenizer_id == "mock-subword"
    assert tok.family == "mock"
    assert tok.vocab_size > 0

    # Clean standard words tokenize as single subwords
    clean_tokens = tok.tokenize("halo dunia saya pergi")
    assert clean_tokens == ["halo", "dunia", "saya", "pergi"]
    assert tok.count_tokens("halo dunia saya pergi") == 4

    # Elongated repeated characters shatter into subwords
    shattered = tok.tokenize("iyaaaa")
    assert len(shattered) > 1
    assert "".join(shattered) == "iyaaaa"
    assert tok.count_tokens("iyaaaa") == len(shattered)

    # Empty string handling
    assert tok.tokenize("") == []
    assert tok.count_tokens("") == 0
    assert tok.tokenize("   ") == []
    assert tok.count_tokens("   ") == 0


def test_tiktoken_adapter_import_guard_or_execution():
    from basa_evals.tokenizers.tiktoken_adapter import TiktokenAdapter

    try:
        import tiktoken  # noqa: F401

        has_tiktoken = True
    except ImportError:
        has_tiktoken = False

    if has_tiktoken:
        tok = TiktokenAdapter("gpt-4o", encoding_name="o200k_base")
        assert isinstance(tok, TokenizerAdapter)
        assert tok.tokenizer_id == "gpt-4o"
        assert tok.family == "bpe"
        assert tok.vocab_size >= 200000
        count = tok.count_tokens("Halo Indonesia!")
        assert count > 0
    else:
        with pytest.raises(ImportError) as exc_info:
            TiktokenAdapter("gpt-4o", encoding_name="o200k_base")
        assert "pip install" in str(exc_info.value) or "tokenizers" in str(exc_info.value)


def test_hf_adapter_import_guard_or_execution():
    from basa_evals.tokenizers.hf_adapter import HuggingFaceTokenizerAdapter

    try:
        import transformers  # noqa: F401

        has_transformers = True
    except ImportError:
        has_transformers = False

    if not has_transformers:
        with pytest.raises(ImportError) as exc_info:
            HuggingFaceTokenizerAdapter("indobert", pretrained_model_name="indobenchmark/indobert-base-p1")
        assert "pip install" in str(exc_info.value) or "tokenizers" in str(exc_info.value)


def test_register_default_tokenizers():
    registry = TokenizerRegistry()
    registry.register_defaults()
    available = registry.list_available()
    assert "mock-subword" in available
    assert "gpt-4o" in available
    assert "llama-3" in available
    assert "indobert" in available
    assert "gemma-2" in available

    # mock-subword should resolve immediately without network/dependencies
    mock_tok = registry.get("mock-subword")
    assert mock_tok.tokenizer_id == "mock-subword"
