import random
from typing import Optional

ADJACENT_KEYS = {
    'a': ['s', 'q', 'z', 'w'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['s', 'e', 'r', 'f', 'c', 'x'],
    'e': ['w', 's', 'd', 'r', '3', '4'],
    'f': ['d', 'r', 't', 'g', 'v', 'c'],
    'g': ['f', 't', 'y', 'h', 'b', 'v'],
    'h': ['g', 'y', 'u', 'j', 'n', 'b'],
    'i': ['u', 'j', 'k', 'o', '8', '9'],
    'j': ['h', 'u', 'i', 'k', 'n', 'm'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p', ';'],
    'm': ['n', 'j', 'k', ','],
    'n': ['b', 'h', 'j', 'm'],
    'o': ['i', 'k', 'l', 'p', '9', '0'],
    'p': ['o', 'l', '[', '0', '-'],
    'q': ['w', 'a', '1', '2'],
    'r': ['e', 'd', 'f', 't', '4', '5'],
    's': ['a', 'w', 'e', 'd', 'x', 'z'],
    't': ['r', 'f', 'g', 'y', '5', '6'],
    'u': ['y', 'h', 'j', 'i', '7', '8'],
    'v': ['c', 'f', 'g', 'b'],
    'w': ['q', 'a', 's', 'e', '2', '3'],
    'x': ['z', 's', 'd', 'c'],
    'y': ['t', 'g', 'h', 'u', '6', '7'],
    'z': ['a', 's', 'x'],
}


class TypoGenerator:
    def __init__(self, typo_rate: float):
        self.typo_rate = typo_rate

    def should_typo(self) -> bool:
        return random.random() < self.typo_rate

    def get_typo_char(self, correct_char: str) -> Optional[str]:
        lower = correct_char.lower()
        if lower not in ADJACENT_KEYS:
            return None
        typo = random.choice(ADJACENT_KEYS[lower])
        if correct_char.isupper():
            return typo.upper()
        return typo
