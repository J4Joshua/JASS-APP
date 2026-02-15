from __future__ import annotations

import numpy as np


def dissonance_tension_from_tis_norm(tis_norm: np.ndarray) -> np.ndarray:
    """Paper-aligned dissonance: smaller ||T|| => more dissonant => more tension."""
    d = -np.asarray(tis_norm, dtype=np.float64)
    return d
