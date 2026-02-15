from __future__ import annotations

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
        out[name] = chroma_bits_to_tis(triad_chroma(pc, quality))
    return out
