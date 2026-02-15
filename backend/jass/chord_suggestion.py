"""Backend-friendly chord suggestion API.

This module exposes a normal Python function (no argparse) so you can reuse the
paper-aligned tonal tension model in a backend.

For CLI usage, see `chord_suggestion_cli.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .chroma_index import (
    CHROMA_LEN,
    ChromaInputError,
    bits_to_mask,
    chroma_bits_to_notes,
    filter_slash_suggestions,
)
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


def _coerce_chroma_bits(chroma: Sequence[int]) -> list[int]:
    bits = [int(x) for x in chroma]
    if len(bits) != CHROMA_LEN:
        raise ChromaInputError(f"Expected chroma length {CHROMA_LEN}, got {len(bits)}.")
    for i, b in enumerate(bits):
        if b not in (0, 1):
            raise ChromaInputError(f"Bits must be 0/1; got {b!r} at index {i}.")
    return bits


def suggest_chords(
    *,
    chord: str | None = None,
    progression: Sequence[str] | None = None,
    key: str,
    chroma: Sequence[int] | None = None,
    index: str | Path | TISIndex = "tis_index.npz",
    top: int = 10,
    goal: str = "resolve",
    weights: Mapping[str, float] | None = None,
    normalize: bool = True,
    voice_leading_addition_penalty: int = 4,
    flats: bool = False,
    include_aliases: bool = False,
    min_notes: int | None = 3,
    max_notes: int | None = 5,
    d3_function_weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Suggest next chords.

    Parameters
    ----------
    chord:
        Current chord name. If ``progression`` is provided and ``chord`` is None,
        it defaults to the last chord of the progression.
    chroma:
        Optional 12-D chroma bit-vector (0/1). If provided, it takes precedence over ``chord``.
    progression:
        Optional progression context ending in ``chord``.
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
    flats:
        If True, spell note names with flats (db/eb/gb/ab/bb).
    include_aliases:
        If True, include alias lists for each result (can be large).
    min_notes, max_notes:
        If set, filters suggestions to chords whose pitch-class set size is within bounds.

    Returns
    -------
    dict with keys: query, goal, weights, results, meta
    """
    idx = _load_index(index)
    key_root, key_mode = parse_key(key)

    prog_list = list(progression) if progression else None
    name_to_row = idx.build_name_to_row()
    mask_to_row = idx.build_mask_to_row()

    chosen_row: int | None = None
    chosen_chord: str | None = None
    chroma_bits: list[int] | None = None

    # If both are provided, chroma takes precedence.
    if chroma is not None:
        chroma_bits = _coerce_chroma_bits(chroma)
        mask = bits_to_mask(chroma_bits)
        row = mask_to_row.get(int(mask))
        if row is None:
            raise ValueError("Provided chroma vector was not found in the chord index.")
        chosen_row = int(row)
        chosen_chord = str(idx.rep_names[chosen_row])

    if chord is not None and chosen_row is None:
        if chord not in name_to_row:
            raise ValueError(f"Chord {chord!r} not found in index.")
        chosen_chord = chord
        chosen_row = int(name_to_row[chord])

    if prog_list:
        last = prog_list[-1]
        if last not in name_to_row:
            raise ValueError(f"Chord {last!r} in progression not found in index.")
        last_row = int(name_to_row[last])
        if chosen_row is None:
            chosen_row = last_row
            chosen_chord = last
        elif last_row != chosen_row:
            raise ValueError("chord/chroma must match the last chord in progression.")

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
        min_notes=min_notes,
        max_notes=max_notes,
        d3_function_weights=dict(d3_function_weights) if d3_function_weights is not None else None,
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
            "chroma": chroma_bits,
            "progression": prog_list,
            "key": f"{key_root} {key_mode}",
        },
        "goal": goal,
        "weights": dict(weights) if weights is not None else dict(DEFAULT_WEIGHTS),
        "d3_function_weights": dict(d3_function_weights) if d3_function_weights is not None else None,
        "results": results,
        "meta": idx.meta,
    }
