from __future__ import annotations

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
    normalize: bool = True,
    min_notes: int | None = None,
    max_notes: int | None = None,
    d3_function_weights: dict[str, float] | None = None,
) -> list[dict]:
    name_to_row = index.build_name_to_row()
    if prev_chord not in name_to_row:
        raise ValueError(f"Chord {prev_chord!r} not found in index.")

    prev_row = name_to_row[prev_chord]
    # Get the weights used for calculation to compute individual contributions.
    active_weights = weights if weights is not None else DEFAULT_WEIGHTS

    feats = compute_features(
        index,
        prev_row,
        key_root,
        key_mode,
        d3_function_weights=d3_function_weights,
    )
    tension = compute_tension(feats, weights=active_weights, normalize=False)
    tension[prev_row] = np.nan

    try:
        target = float(goal)
        sort_key = np.abs(tension - target)
    except (ValueError, TypeError):
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
            "tension": float(tension[i]),
        }
        
        # Merge the weighted contributions into the result dictionary
        res.update(weighted_contribs)
        results.append(res)
        
        if len(results) >= top:
            break
    return results
