"""Paper-aligned tonal tension model utilities.

This package factors the Entropy 2020 (Navarro-Cáceres et al.)-aligned pieces
out of the CLI scripts so they are easy to tune and reuse.
"""

from .features import compute_features
from .theory import parse_key, key_tis, function_prototypes, roman_to_chord
from .weights import DEFAULT_WEIGHTS, DEFAULT_WEIGHTS_NORMALIZED, PAPER_WEIGHTS_TABLE1
from .model import compute_tension, suggest_next_chords

__all__ = [
    "DEFAULT_WEIGHTS",
    "DEFAULT_WEIGHTS_NORMALIZED",
    "PAPER_WEIGHTS_TABLE1",
    "compute_features",
    "compute_tension",
    "function_prototypes",
    "key_tis",
    "parse_key",
    "roman_to_chord",
    "suggest_next_chords",
]
