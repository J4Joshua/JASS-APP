from __future__ import annotations


PAPER_WEIGHTS_TABLE1: dict[str, float] = {
    # From Table 1 (Experiment 1): statistically significant indicators.
    # Tonal distance (from the key) -> d2
    # Dissonance -> c
    "d1": 0.4,
    "d2": 2,
    "d3": 1.4,
    "c": 2,
}

PAPER_WEIGHTS_TABLE2: dict[str, float] = {
    # From Table 2 (Experiment 2): statistically significant indicators.
    # Tonal distance (from the key) -> d2
    # Dissonance -> c
    "d1": 1.1,
    "d2": 2.9,
    "d3": 1.4,
    "c": 1.3,
}

def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = float(sum(float(x) for x in weights.values()))
    if total <= 0:
        return dict(weights)
    return {k: float(v) / total for k, v in weights.items()}

DEFAULT_WEIGHTS: dict[str, float] = dict(PAPER_WEIGHTS_TABLE1)
DEFAULT_WEIGHTS_NORMALIZED: dict[str, float] = normalize_weights(PAPER_WEIGHTS_TABLE1)