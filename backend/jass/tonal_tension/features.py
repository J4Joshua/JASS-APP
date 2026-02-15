from __future__ import annotations

from typing import Mapping

import numpy as np

from ..tis_index import TISIndex
from ..tis_metrics import vectorized_angles
from .dissonance import dissonance_tension_from_tis_norm
from .theory import function_prototypes, key_tis


_D3_FUNCTION_WEIGHTS: dict[str, float] = {
    # Keys must match `function_prototypes(...)`: "tonic", "subdominant", "dominant".
    # Larger weight => distance-from-that-function matters more in `d3`.
    "tonic": 1.2,
    "subdominant": 1.0,
    "dominant": 1.2,
}


def compute_features(
    index: TISIndex,
    prev_row: int,
    key_root: str,
    key_mode: str,
    *,
    d3_function_weights: Mapping[str, float] | None = None,
) -> dict[str, np.ndarray]:
    """Compute paper-aligned tension indicators for every chord in the index."""
    n = index.tis.shape[0]
    prev_tis = index.tis[prev_row]

    diff = index.tis - prev_tis[None, :]
    d1 = np.sqrt(np.sum(np.abs(diff) ** 2, axis=1)) # this is the euclidean distance between the current chord and the previous one.

    k_tis = key_tis(key_root, key_mode)
    d2 = vectorized_angles(index.tis_unit, k_tis) # distance from the vectorized tonal key

    protos = function_prototypes(key_root, key_mode)
    offset = index.tis - k_tis[None, :]
    offset_norm = np.sqrt(np.sum(np.abs(offset) ** 2, axis=1))
    offset_unit = np.zeros_like(offset)
    good = offset_norm > 0
    offset_unit[good] = offset[good] / offset_norm[good, None]

    # d3 is based on I / IV / V prototypes (Section 3.2).
    # We use a weighted mean of the three prototype angles so changing the weights
    # affects `d3` in a predictable way.
    eff_d3_weights = d3_function_weights if d3_function_weights is not None else _D3_FUNCTION_WEIGHTS
    d3_weighted = np.zeros(n, dtype=np.float64)
    d3_total_w = 0.0
    for func_name, proto in protos.items():
        proto_off = proto - k_tis
        angles = vectorized_angles(offset_unit, proto_off)
        w = float(eff_d3_weights.get(str(func_name), 1.0))
        if w == 0.0:
            continue
        d3_weighted += w * angles
        d3_total_w += w
    d3 = d3_weighted / d3_total_w if d3_total_w > 0 else np.full(n, np.nan, dtype=np.float64)

    c = dissonance_tension_from_tis_norm(index.tis_norm)
    print(c)

    return {"d1": d1, "d2": d2, "d3": d3, "c": c}
