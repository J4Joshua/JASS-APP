"""Backend-friendly chord suggestion API.

This module exposes a normal Python function (no argparse) so you can reuse the
paper-aligned tonal tension model in a backend.

For CLI usage, see `chord_suggestion_cli.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .chroma_index import bits_to_mask, chroma_bits_to_notes, filter_slash_suggestions
from .tis_index import TISIndex
from .tonal_tension import DEFAULT_WEIGHTS, parse_key
from .tonal_tension.model import suggest_next_chords as _suggest_next_chords


def _load_index(index: str | Path | TISIndex) -> TISIndex:
    if isinstance(index, TISIndex):
        return index
    index_path = Path(index)
    if not index_path.is_absolute() and not index_path.exists():
        candidate = Path(__file__).resolve().parent / index_path
        if candidate.exists():
            index_path = candidate
    return TISIndex.from_npz(index_path)


def suggest_chords(
    *,
    chord: str | None = None,
    chroma: Sequence[int] | None = None,
    progression: Sequence[str] | None = None,
    key: str,
    index: str | Path | TISIndex = "tis_index.npz",
    top: int = 10,
    goal: str = "resolve",
    weights: Mapping[str, float] | None = None,
    normalize: bool = True,
    voice_leading_addition_penalty: int = 4,
    flats: bool = False,
    include_aliases: bool = False,
) -> dict[str, Any]:
    """Suggest next chords.

    Parameters
    ----------
    chord:
        Current chord name. If ``progression`` is provided and ``chord`` is None,
        it defaults to the last chord of the progression.
    progression:
        Optional progression context ending in ``chord``. If provided, hierarchical
        tension is computed for each candidate as if appended.
    key:
        Human-friendly key string, e.g. ``"C"``, ``"Am"``, ``"F# minor"``.
    index:
        Path to ``tis_index.npz`` or an in-memory ``TISIndex``.
    top:
        Number of results to return.
    goal:
        ``"resolve"`` (low tension), ``"build"`` (high tension), or a numeric string target.
    weights:
        Optional override mapping for feature weights.
    normalize:
        If True, min-max normalizes each feature before weighting.
    voice_leading_addition_penalty:
        Insertion/deletion semitone penalty for voice-leading when chord sizes differ.
    flats:
        If True, spell note names with flats (db/eb/gb/ab/bb).
    include_aliases:
        If True, include alias lists for each result (can be large).

    Returns
    -------
    dict with keys: query, goal, weights, results, meta
    """
    idx = _load_index(index)
    key_root, key_mode = parse_key(key)

    prog_list = list(progression) if progression else None
    chosen_chord = chord
    if prog_list:
        if chosen_chord is None:
            chosen_chord = prog_list[-1]
        elif chosen_chord != prog_list[-1]:
            raise ValueError("chord must match the last chord in progression.")

    # Resolve prev_row from chroma if provided, bypassing name lookup
    resolved_row: int | None = None
    if chroma is not None:
        mask = bits_to_mask(list(chroma))
        mask_to_row = idx.build_mask_to_row()
        resolved_row = mask_to_row.get(mask)
        if resolved_row is None:
            raise ValueError(f"Chroma {list(chroma)} not found in index.")
        if chosen_chord is None:
            chosen_chord = str(idx.rep_names[resolved_row])

    if chosen_chord is None:
        raise ValueError("Either chord, chroma, or progression must be provided.")

    results = _suggest_next_chords(
        idx,
        prev_chord=chosen_chord,
        key_root=key_root,
        key_mode=key_mode,
        top=top,
        weights=dict(weights) if weights is not None else None,
        goal=goal,
        progression=prog_list,
        normalize=normalize,
        voice_leading_addition_penalty=voice_leading_addition_penalty,
        prev_row=resolved_row,
    )

    # Post-process notes + aliases for backend convenience.
    for r in results:
        row = int(r["row"])
        if flats:
            r["notes"] = chroma_bits_to_notes(idx.chroma_bits[row].tolist(), flats=True)
        if include_aliases:
            r["aliases"] = idx.aliases_for_row(row)
        else:
            r["aliases_count"] = int(idx.alias_offsets[row + 1] - idx.alias_offsets[row])
        r["representatives_all"] = idx.reps_for_row(row)
        r["representatives"] = filter_slash_suggestions(r["representatives_all"])

    return {
        "query": {
            "chord": chosen_chord,
            "progression": prog_list,
            "key": f"{key_root} {key_mode}",
        },
        "goal": goal,
        "weights": dict(weights) if weights is not None else dict(DEFAULT_WEIGHTS),
        "results": results,
        "meta": idx.meta,
    }
