from __future__ import annotations

from typing import Sequence

import numpy as np

from ..chroma_index import chroma_bits_to_notes, filter_slash_suggestions
from ..tis_index import TISIndex
from .features import compute_features
from .weights import DEFAULT_WEIGHTS

rng = np.random.default_rng()

def minmax01(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    finite = np.isfinite(x)
    out = np.full_like(x, np.nan, dtype=np.float64)
    if not np.any(finite):
        return out
    xmin = float(np.min(x[finite]))
    xmax = float(np.max(x[finite]))
    span = xmax - xmin
    if span > 0:
        out[finite] = (x[finite] - xmin) / span
    else:
        # all finite values are equal -> treat as 0 everywhere
        out[finite] = 0.0
    return out


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
        w_f = float(w)
        if w_f == 0.0:
            continue
        vals = features.get(key)
        if vals is None:
            continue
        if normalize:
            vals = np.asarray(vals, dtype=np.float64)
            finite = np.isfinite(vals)
            if not np.any(finite):
                continue
            vmin = float(np.min(vals[finite]))
            vmax = float(np.max(vals[finite]))
            span = vmax - vmin
            if span > 0:
                normed = np.zeros_like(vals, dtype=np.float64)
                normed[finite] = (vals[finite] - vmin) / span
            else:
                normed = np.zeros_like(vals, dtype=np.float64)
            tension += w_f * normed
        else:
            tension += w_f * vals  # float of weights times value
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
    min_notes: int | None = None,
    max_notes: int | None = None,
    d3_function_weights: dict[str, float] | None = None,
) -> list[dict]:
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
            progression_rows.append(int(name_to_row[name]))
        if progression_rows and progression_rows[-1] != prev_row:
            raise ValueError("progression must end with prev_chord.")

    # Get the weights used for calculation to compute individual contributions.
    active_weights = weights if weights is not None else DEFAULT_WEIGHTS
    include_m = float(active_weights.get("m", 0.0)) != 0.0
    include_h = float(active_weights.get("h", 0.0)) != 0.0

    feats = compute_features(
        index,
        prev_row,
        key_root,
        key_mode,
        progression_rows=progression_rows,
        voice_leading_addition_penalty=voice_leading_addition_penalty,
        include_m=include_m,
        include_h=include_h,
        d3_function_weights=d3_function_weights,
    )
    tension_raw = compute_tension(feats, weights=active_weights, normalize=normalize)
    tension_raw[prev_row] = np.nan

    # Normalize final tension to [0, 1] so numeric goals are meaningful on that scale
    tension = minmax01(tension_raw)

    if goal == "tension":
        goal = 0.3 + rng.uniform(low=-0.05, high=0.05, size=None)
    elif goal == "resolve":
        goal = 0.1 + rng.uniform(low=-0.05, high=0.05, size=None)
    elif goal == "resonant":
        goal = 0.2 + rng.uniform(low=-0.05, high=0.06, size=None)

    try:
        target = float(goal)  # expected to be in [0, 1]
        sort_key = np.abs(tension - target)
    except (ValueError, TypeError):
        # "build" -> high tension, "resolve" -> low tension
        sort_key = -tension if goal == "build" else tension

    order = np.argsort(np.where(np.isnan(sort_key), np.inf, sort_key))

    results: list[dict] = []
    rank = 0

    for idx_i in order:
        i = int(idx_i)
        note_count = int(np.sum(index.chroma_bits[i] != 0))
        if min_notes is not None and note_count < int(min_notes):
            continue
        if max_notes is not None and note_count > int(max_notes):
            continue
        reps_all = index.reps_for_row(i)
        reps = filter_slash_suggestions(reps_all)
        notes = chroma_bits_to_notes(index.chroma_bits[i].tolist())
        weighted_contribs = {}
        for feat_key, w in active_weights.items():
            w_f = float(w)
            if w_f == 0.0:
                continue
            if feat_key not in feats:
                continue
            val = feats[feat_key][i]
            if normalize:
                # To be perfectly accurate to compute_tension, 
                # we'd need the global min/max for each feature
                vals = feats[feat_key]
                vals = np.asarray(vals, dtype=np.float64)
                finite = np.isfinite(vals)
                if np.any(finite):
                    vmin = float(np.min(vals[finite]))
                    vmax = float(np.max(vals[finite]))
                    span = vmax - vmin
                    normed = (float(val) - vmin) / span if span > 0 and np.isfinite(val) else 0.0
                else:
                    normed = 0.0
                weighted_contribs[f"w_{feat_key}"] = w_f * float(normed)
            else:
                weighted_contribs[f"w_{feat_key}"] = w_f * float(val)
        rank += 1
        res = {
            "row": i,
            "rank": rank,
            "name": reps[0] if reps else str(index.rep_names[i]),
            "reps": reps,
            "notes": notes,
            "d1": float(feats["d1"][i]),
            "d2": float(feats["d2"][i]),
            "d3": float(feats["d3"][i]),
            "c": float(feats["c"][i]),
            "tension_raw": float(tension_raw[i]),
            "tension": float(tension[i]),  # normalized 0..1

        }
        
        # Merge the weighted contributions into the result dictionary
        res.update(weighted_contribs)
        results.append(res)
        
        if len(results) >= top:
            break
    return results
