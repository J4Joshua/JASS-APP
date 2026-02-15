from __future__ import annotations

from typing import Sequence

import numpy as np

from ..tis_index import TISIndex
from ..tis_metrics import vectorized_angles
from .dissonance import dissonance_tension_from_tis_norm
from .hierarchy import harmonic_function_label_from_tis, hierarchical_tension_last
from .theory import function_prototypes, key_tis
from .voice_leading import voice_leading_tension


def compute_features(
    index: TISIndex,
    prev_row: int,
    key_root: str,
    key_mode: str,
    *,
    progression_rows: Sequence[int] | None = None,
    voice_leading_addition_penalty: int = 4,
) -> dict[str, np.ndarray]:
    """Compute paper-aligned tension indicators for every chord in the index."""
    n = index.tis.shape[0]
    prev_tis = index.tis[prev_row]
    prev_bits = index.chroma_bits[prev_row].tolist()

    diff = index.tis - prev_tis[None, :]
    d1 = np.sqrt(np.sum(np.abs(diff) ** 2, axis=1)) # this is the euclidean distance between the current chord and the previous one.

    k_tis = key_tis(key_root, key_mode)
    d2 = vectorized_angles(index.tis_unit, k_tis) # 

    protos = function_prototypes(key_root, key_mode)
    offset = index.tis - k_tis[None, :]
    offset_norm = np.sqrt(np.sum(np.abs(offset) ** 2, axis=1))
    offset_unit = np.zeros_like(offset)
    good = offset_norm > 0
    offset_unit[good] = offset[good] / offset_norm[good, None]
    d3 = np.full(n, np.inf, dtype=np.float64)
    for proto in protos.values():
        proto_off = proto - k_tis
        d3 = np.minimum(d3, vectorized_angles(offset_unit, proto_off))

    c = dissonance_tension_from_tis_norm(index.tis_norm)

    m = np.zeros(n, dtype=np.float64)
    for i in range(n):
        if i == prev_row:
            continue
        m[i] = voice_leading_tension(
            prev_bits,
            index.chroma_bits[i].tolist(),
            addition_penalty=voice_leading_addition_penalty,
        )

    h = np.zeros(n, dtype=np.float64)
    if progression_rows:
        prog_rows = list(map(int, progression_rows))
        prog_tis = [index.tis[r] for r in prog_rows]
        prog_funcs = [harmonic_function_label_from_tis(t, protos) for t in prog_tis]
        prog_d2 = [float(d2[r]) for r in prog_rows]
        for i in range(n):
            if i == prev_row:
                continue
            cand_tis = index.tis[i]
            cand_func = harmonic_function_label_from_tis(cand_tis, protos)
            cand_d2 = float(d2[i])
            h[i] = hierarchical_tension_last(
                tis_list=prog_tis + [cand_tis],
                func_labels=prog_funcs + [cand_func],
                key_distances=prog_d2 + [cand_d2],
            )

    return {"d1": d1, "d2": d2, "d3": d3, "c": c, "m": m, "h": h}
