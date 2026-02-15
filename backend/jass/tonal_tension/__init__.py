"""Paper-aligned tonal tension model utilities.

This package factors the Entropy 2020 (Navarro-Cáceres et al.)-aligned pieces
out of the CLI scripts so they are easy to tune and reuse.
"""

from .features import compute_features
from .hierarchy import hierarchical_tension_last, harmonic_function_label_from_tis
from .theory import parse_key, key_tis, function_prototypes
from .weights import DEFAULT_WEIGHTS, PAPER_WEIGHTS_TABLE1
from .model import compute_tension, suggest_next_chords

__all__ = [
    "DEFAULT_WEIGHTS",
    "PAPER_WEIGHTS_TABLE1",
    "compute_features",
    "compute_tension",
    "function_prototypes",
    "harmonic_function_label_from_tis",
    "hierarchical_tension_last",
    "key_tis",
    "parse_key",
    "suggest_next_chords",
]

