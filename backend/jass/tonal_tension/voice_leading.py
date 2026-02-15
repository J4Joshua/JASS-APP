from __future__ import annotations

import itertools
from typing import Sequence

import numpy as np

from ..tis_index import chroma_bits_to_tis, euclidean_distance


PC_DIST = np.zeros((12, 12), dtype=np.int32)
for _i in range(12):
    for _j in range(12):
        _d = abs(_i - _j)
        PC_DIST[_i, _j] = min(_d, 12 - _d)


def _chroma_to_pc_list(bits: Sequence[int]) -> list[int]:
    return [i for i, b in enumerate(bits) if b]


NOTE_TIS: list[np.ndarray] = []
for _pc in range(12):
    _bits = [0] * 12
    _bits[_pc] = 1
    NOTE_TIS.append(chroma_bits_to_tis(_bits))
NOTE_TIS_NORM = float(np.sqrt(np.sum(np.abs(NOTE_TIS[0]) ** 2)))


def voice_leading_tension(
    bits_a: Sequence[int],
    bits_b: Sequence[int],
    *,
    addition_penalty: int = 4,
) -> float:
    """Paper-aligned core of Eq. (8), adapted to pitch-class sets (no voicings).

    Returns a tension-increasing value by negating the paper's stability sum.
    """
    pcs_a = _chroma_to_pc_list(bits_a)
    pcs_b = _chroma_to_pc_list(bits_b)
    if not pcs_a or not pcs_b:
        return 0.0

    na, nb = len(pcs_a), len(pcs_b)
    n = max(na, nb)

    cost = np.full((n, n), addition_penalty * NOTE_TIS_NORM, dtype=np.float64)
    for i in range(na):
        for j in range(nb):
            s = float(PC_DIST[pcs_a[i], pcs_b[j]])
            mu = euclidean_distance(NOTE_TIS[pcs_a[i]], NOTE_TIS[pcs_b[j]])
            cost[i, j] = s * mu

    try:
        from scipy.optimize import linear_sum_assignment  # type: ignore[import-untyped]

        row_ind, col_ind = linear_sum_assignment(cost)
        chosen = cost[row_ind, col_ind]
    except ImportError:
        if n <= 8:
            best = None
            for perm in itertools.permutations(range(n)):
                total = sum(cost[i, perm[i]] for i in range(n))
                if best is None or total < best:
                    best = total
                    best_perm = perm
            chosen = np.array([cost[i, best_perm[i]] for i in range(n)], dtype=np.float64)
        else:
            used_r: set[int] = set()
            used_c: set[int] = set()
            picked: list[float] = []
            flat = sorted((cost[i, j], i, j) for i in range(n) for j in range(n))
            for c_val, i, j in flat:
                if i not in used_r and j not in used_c:
                    picked.append(float(c_val))
                    used_r.add(i)
                    used_c.add(j)
                    if len(used_r) == n:
                        break
            chosen = np.array(picked, dtype=np.float64)

    stability = float(np.sum(np.exp(-0.05 * chosen)))
    return -stability
