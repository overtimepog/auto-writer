import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.engine.typo_generator import TypoGenerator, ADJACENT_KEYS


def test_should_typo_always():
    gen = TypoGenerator(typo_rate=1.0)
    for _ in range(50):
        assert gen.should_typo() is True


def test_should_typo_never():
    gen = TypoGenerator(typo_rate=0.0)
    for _ in range(50):
        assert gen.should_typo() is False


def test_get_typo_char_returns_adjacent():
    gen = TypoGenerator(typo_rate=1.0)
    valid_adjacent = set(ADJACENT_KEYS['a'])
    for _ in range(30):
        result = gen.get_typo_char('a')
        assert result in valid_adjacent, f"'{result}' not in expected adjacent keys for 'a'"


def test_get_typo_char_preserves_case():
    gen = TypoGenerator(typo_rate=1.0)
    # Run several times; every result must be uppercase
    for _ in range(30):
        result = gen.get_typo_char('A')
        assert result is not None
        assert result.isupper(), f"Expected uppercase typo for 'A', got '{result}'"


def test_get_typo_char_non_alpha_returns_none():
    gen = TypoGenerator(typo_rate=1.0)
    # Digits and special chars that are NOT in ADJACENT_KEYS as keys should return None
    for ch in ['1', '!', ' ', '\t']:
        result = gen.get_typo_char(ch)
        assert result is None, f"Expected None for '{ch}', got '{result}'"


def test_get_typo_char_unknown_returns_none():
    gen = TypoGenerator(typo_rate=1.0)
    # Characters that exist as keys but uppercase versions map through lower;
    # a truly absent character (e.g. accented letter) should return None
    result = gen.get_typo_char('é')
    assert result is None
