from __future__ import annotations


PAPER_WEIGHTS_TABLE1: dict[str, float] = {
    # From Table 1 (Experiment 1): statistically significant indicators.
    # Tonal distance (from the key) -> d2
    # Dissonance -> c
    # Voice Leading -> m
    # Hierarchical Tension -> h
    "d1": 0.0,
    "d2": 0.158,
    "d3": 0.0,
    "c": 0.303,
    "m": 0.271,
    "h": 0.318,
}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = float(sum(float(x) for x in weights.values()))
    if total <= 0:
        return dict(weights)
    return {k: float(v) / total for k, v in weights.items()}


DEFAULT_WEIGHTS: dict[str, float] = normalize_weights(PAPER_WEIGHTS_TABLE1)

