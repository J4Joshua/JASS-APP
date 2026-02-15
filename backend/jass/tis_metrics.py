from __future__ import annotations

import numpy as np


def vectorized_angles(vectors: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Compute angles (radians) between each row of `vectors` and `ref`.

    Uses the same complex inner-product magnitude convention as `jass.tis_index.angle`.
    """
    vectors = np.asarray(vectors)
    ref = np.asarray(ref)
    if vectors.ndim != 2:
        raise ValueError(f"vectors must be a 2D array; got shape {vectors.shape}.")
    if ref.ndim != 1:
        raise ValueError(f"ref must be a 1D array; got shape {ref.shape}.")
    if vectors.shape[1] != ref.shape[0]:
        raise ValueError(f"Expected vectors.shape[1] == ref.shape[0]; got {vectors.shape} vs {ref.shape}.")

    dots = np.sum(vectors * np.conj(ref)[None, :], axis=1)
    v_norm = np.sqrt(np.sum(np.abs(vectors) ** 2, axis=1))
    r_norm = float(np.sqrt(np.sum(np.abs(ref) ** 2)))
    denom = v_norm * r_norm

    out = np.full(vectors.shape[0], np.nan, dtype=np.float64)
    good = denom > 0
    if np.any(good):
        cos = np.abs(dots[good]) / denom[good]
        cos = np.clip(cos, 0.0, 1.0)
        out[good] = np.arccos(cos).astype(np.float64, copy=False)
    return out

