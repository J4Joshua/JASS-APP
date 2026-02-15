from __future__ import annotations

from typing import Sequence

import numpy as np

from ..chroma_index import chroma_bits_to_notes, filter_slash_suggestions
from ..tis_index import TISIndex
from .features import compute_features
from .weights import DEFAULT_WEIGHTS


def compute_tension(
    features: dict[str, np.ndarray],
    *,
    weights: dict[str, float] | None = None,
    normalize: bool = True,
) -> np.ndarray:
    if weights is None:
        weights = DEFAULT_WEIGHTS

    tension = np.zeros_like(features["d1"])
    for key, w in weights.items():
        vals = features[key]
        if normalize:
            vmin, vmax = float(np.nanmin(vals)), float(np.nanmax(vals))
            span = vmax - vmin
            normed = (vals - vmin) / span if span > 0 else np.zeros_like(vals)
            tension += float(w) * normed
        else:
            tension += float(w) * vals
    return tension


def suggest_next_chords(
    index: TISIndex,
    prev_chord: str,
    key_root: str,
    key_mode: str = "major",
    *,
    top: int = 10,
    weights: dict[str, float] | None = None,
    goal: str = "resolve",
    progression: Sequence[str] | None = None,
    normalize: bool = True,
    voice_leading_addition_penalty: int = 4,
    prev_row: int | None = None,
) -> list[dict]:
    if prev_row is None:
        name_to_row = index.build_name_to_row()
        if prev_chord not in name_to_row:
            raise ValueError(f"Chord {prev_chord!r} not found in index.")
        prev_row = name_to_row[prev_chord]
    progression_rows: list[int] | None = None
    if progression:
        progression_rows = []
        for name in progression:
            if name not in name_to_row:
                raise ValueError(f"Chord {name!r} in progression not found in index.")
            progression_rows.append(name_to_row[name])
        if progression_rows and progression_rows[-1] != prev_row:
            raise ValueError("progression must end with prev_chord.")

    feats = compute_features(
        index,
        prev_row,
        key_root,
        key_mode,
        progression_rows=progression_rows,
        voice_leading_addition_penalty=voice_leading_addition_penalty,
    )
    tension = compute_tension(feats, weights=weights, normalize=normalize)
    tension[prev_row] = np.nan

    try:
        target = float(goal)
        sort_key = np.abs(tension - target)
    except (ValueError, TypeError):
        sort_key = -tension if goal == "build" else tension

    order = np.argsort(np.where(np.isnan(sort_key), np.inf, sort_key))

    results: list[dict] = []
    for rank, idx_i in enumerate(order[:top]):
        i = int(idx_i)
        reps_all = index.reps_for_row(i)
        reps = filter_slash_suggestions(reps_all)
        notes = chroma_bits_to_notes(index.chroma_bits[i].tolist())
        results.append(
            {
                "row": i,
                "rank": rank + 1,
                "name": reps[0] if reps else str(index.rep_names[i]),
                "reps": reps,
                "notes": notes,
                "d1": float(feats["d1"][i]),
                "d2": float(feats["d2"][i]),
                "d3": float(feats["d3"][i]),
                "c": float(feats["c"][i]),
                "m": float(feats["m"][i]),
                "h": float(feats["h"][i]),
                "tension": float(tension[i]),
            }
        )
    return results
