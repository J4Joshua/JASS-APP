from __future__ import annotations

import re
from typing import Sequence

import numpy as np

from ..tis_index import chroma_bits_to_tis


PC_TO_IDX: dict[str, int] = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
    "B#": 0,
}

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# ── Roman-numeral → chord helpers ──────────────────────────────────────────

_LETTERS = ["C", "D", "E", "F", "G", "A", "B"]
_LETTER_TO_BASE_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

_ROMAN_UPPER = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}
_ROMAN_RE = re.compile(
    r"^([b#]?)"
    r"(VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)"
    r"(.*)$",
)


def _has_quality_prefix(suffix: str) -> bool:
    """Return True if *suffix* already encodes root quality (m, ø, dim …)."""
    if suffix.startswith(("ø", "°", "dim", "aug", "+")):
        return True
    if suffix.startswith("m") and not suffix.startswith("maj"):
        return True
    return False


def _build_scale_notes(root: str, mode: str) -> list[str]:
    """Return the 7 scale-note names for *root*/*mode* with correct spelling."""
    root_pc = PC_TO_IDX[root]
    intervals = MAJOR_INTERVALS if mode == "major" else MINOR_INTERVALS

    root_letter_idx = _LETTERS.index(root[0].upper())
    notes: list[str] = []
    for degree, interval in enumerate(intervals):
        target_pc = (root_pc + interval) % 12
        letter = _LETTERS[(root_letter_idx + degree) % 7]
        diff = (target_pc - _LETTER_TO_BASE_PC[letter]) % 12
        if diff == 0:
            notes.append(letter)
        elif diff == 1:
            notes.append(letter + "#")
        elif diff == 11:            # -1 mod 12
            notes.append(letter + "b")
        elif diff == 2:
            notes.append(letter + "##")
        elif diff == 10:
            notes.append(letter + "bb")
        else:
            # Extreme enharmonic – fall back to flat-preference name
            _FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F",
                           "Gb", "G", "Ab", "A", "Bb", "B"]
            notes.append(_FLAT_NAMES[target_pc])
    return notes


def _apply_accidental(note: str, accidental: str) -> str:
    """Apply ``'b'`` or ``'#'`` to an already-spelled note name."""
    if not accidental:
        return note
    existing = note[1:]  # e.g. '', '#', 'b'
    letter = note[0]
    if accidental == "b":
        remap = {"#": "", "": "b", "b": "bb", "##": "#"}
    else:
        remap = {"b": "", "": "#", "#": "##", "bb": "b"}
    return letter + remap.get(existing, existing)


def roman_to_chord(numeral: str, key: str) -> str:
    """Convert a Roman-numeral chord symbol to a concrete chord name in *key*.

    >>> roman_to_chord("ii7", "C")
    'Dm7'
    >>> roman_to_chord("V7", "C")
    'G7'
    >>> roman_to_chord("Imaj7", "C")
    'Cmaj7'
    >>> roman_to_chord("bII7", "C")
    'Db7'
    """
    root, mode = parse_key(key)

    m = _ROMAN_RE.match(numeral)
    if not m:
        raise ValueError(f"Cannot parse Roman numeral: {numeral!r}")

    accidental, roman, suffix = m.groups()
    degree = _ROMAN_UPPER[roman.upper()]
    is_minor = roman.islower()

    note = _apply_accidental(_build_scale_notes(root, mode)[degree], accidental)

    if is_minor and not _has_quality_prefix(suffix):
        suffix = "m" + suffix

    return note + suffix


# Diatonic triad quality per scale degree (offset from tonic)
MAJOR_TRIAD_MAP: dict[int, str] = {
    0: "major",
    2: "minor",
    4: "minor",
    5: "major",
    7: "major",
    9: "minor",
    11: "diminished",
}
MINOR_TRIAD_MAP: dict[int, str] = {
    0: "minor",
    2: "diminished",
    3: "major",
    5: "minor",
    7: "minor",
    8: "major",
    10: "major",
}


def triad_chroma(root_pc: int, quality: str) -> list[int]:
    intervals = {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        "diminished": [0, 3, 6],
        "augmented": [0, 4, 8],
    }[quality]
    bits = [0] * 12
    for iv in intervals:
        bits[(root_pc + iv) % 12] = 1
    return bits


def parse_key(key_str: str) -> tuple[str, str]:
    """Parse a human-friendly key string into (root, mode)."""
    s = key_str.strip()

    parts = s.split()
    if len(parts) == 2:
        root_str, mode_str = parts
        mode_str = mode_str.lower()
        if mode_str in ("major", "maj"):
            return (root_str, "major")
        if mode_str in ("minor", "min"):
            return (root_str, "minor")

    for suffix, mode in [("min", "minor"), ("maj", "major")]:
        if s.lower().endswith(suffix):
            root_str = s[: -len(suffix)]
            if root_str in PC_TO_IDX:
                return (root_str, mode)

    if s.endswith("m") and len(s) >= 2:
        root_str = s[:-1]
        if root_str in PC_TO_IDX:
            return (root_str, "minor")

    if s in PC_TO_IDX:
        return (s, "major")

    raise ValueError(f"Cannot parse key: {key_str!r}")


def key_chroma(root: str, mode: str = "major") -> list[int]:
    root_idx = PC_TO_IDX[root]
    intervals = MAJOR_INTERVALS if mode == "major" else MINOR_INTERVALS
    bits = [0] * 12
    for iv in intervals:
        bits[(root_idx + iv) % 12] = 1
    return bits


def key_tis(root: str, mode: str = "major") -> np.ndarray:
    return chroma_bits_to_tis(key_chroma(root, mode))


def function_prototypes(root: str, mode: str = "major") -> dict[str, np.ndarray]:
    """Paper uses I/IV/V as prototypes for tonic/subdominant/dominant (Section 3.2)."""
    root_idx = PC_TO_IDX[root]
    triad_map = MAJOR_TRIAD_MAP if mode == "major" else MINOR_TRIAD_MAP

    degrees = {
        "tonic": 0,  # I / i
        "subdominant": 5,  # IV / iv
        "dominant": 7,  # V / v (diatonic)
    }

    out: dict[str, np.ndarray] = {}
    for name, deg in degrees.items():
        pc = (root_idx + deg) % 12
        quality = triad_map[deg]
        # print(triad_chroma(pc, quality))
        # this is correct, gives major tonal, subdominant, and dominant.
        out[name] = chroma_bits_to_tis(triad_chroma(pc, quality))
    return out
