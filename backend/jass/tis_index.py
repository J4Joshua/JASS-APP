from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .chroma_index import (
    CHROMA_LEN,
    ChromaInputError,
    bits_to_mask,
    choose_representatives_by_root,
    choose_representative,
)


TIS_DIM = CHROMA_LEN // 2
DEFAULT_WEIGHTS = np.array([2, 11, 17, 16, 19, 7], dtype=np.float64)
DEFAULT_BIT_ORDER = np.array(
    ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"], dtype="<U2"
)


def dot(v1: np.ndarray, v2: np.ndarray) -> np.complex128:
    v1 = np.asarray(v1)
    v2 = np.asarray(v2)
    if v1.shape != v2.shape:
        raise ValueError(f"dot expects equal shapes, got {v1.shape} vs {v2.shape}.")
    return np.sum(v1 * np.conj(v2))


def norm(v: np.ndarray) -> float:
    v = np.asarray(v)
    return float(np.sqrt(np.real(dot(v, v))))


def euclidean_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    v1 = np.asarray(v1)
    v2 = np.asarray(v2)
    if v1.shape != v2.shape:
        raise ValueError(f"distance expects equal shapes, got {v1.shape} vs {v2.shape}.")
    diff = v1 - v2
    return float(np.sqrt(np.sum(np.abs(diff) ** 2)))


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Returns a real-valued similarity in [0, 1] using complex inner product magnitude.
    """
    denom = norm(v1) * norm(v2)
    if denom == 0:
        raise ValueError("cosine_similarity undefined for zero-norm vector.")
    return float(np.clip(np.abs(dot(v1, v2)) / denom, 0.0, 1.0))


def angle(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Angle (radians) derived from cosine_similarity.
    """
    return float(np.arccos(np.clip(cosine_similarity(v1, v2), 0.0, 1.0)))


def _tis_exponent_matrix(chroma_len: int = CHROMA_LEN) -> np.ndarray:
    if chroma_len % 2 != 0:
        raise ValueError("Expected even chroma length.")
    k = np.arange(1, chroma_len // 2 + 1, dtype=np.float64)[:, None]  # (6,1)
    n = np.arange(0, chroma_len, dtype=np.float64)[None, :]  # (1,12)
    return np.exp(-2j * np.pi * k * n / chroma_len).astype(np.complex128)  # (6,12)


_E12 = _tis_exponent_matrix(CHROMA_LEN)


def chroma_matrix_to_tis(
    chroma_bits: np.ndarray, *, weights: np.ndarray = DEFAULT_WEIGHTS
) -> np.ndarray:
    """
    Vectorized chroma->TIS for many chords.
      chroma_bits: (N,12) of 0/1.
      returns: (N,6) complex128
    """
    chroma_bits = np.asarray(chroma_bits)
    if chroma_bits.ndim != 2 or chroma_bits.shape[1] != CHROMA_LEN:
        raise ChromaInputError(f"Expected shape (N,{CHROMA_LEN}); got {chroma_bits.shape}.")

    if not np.issubdtype(chroma_bits.dtype, np.integer) and not np.issubdtype(
        chroma_bits.dtype, np.floating
    ):
        raise ChromaInputError("chroma_bits must be numeric.")

    chroma_bits = chroma_bits.astype(np.float64, copy=False)
    sums = chroma_bits.sum(axis=1, keepdims=True)
    if np.any(sums == 0):
        raise ChromaInputError("chroma vector must have at least one active pitch class.")
    chroma_bar = chroma_bits / sums

    weights = np.asarray(weights, dtype=np.float64)
    if weights.shape != (TIS_DIM,):
        raise ValueError(f"weights must have shape ({TIS_DIM},); got {weights.shape}.")

    tis = chroma_bar @ _E12.T  # (N,6)
    tis = tis * weights[None, :]
    return tis.astype(np.complex128, copy=False)


def chroma_bits_to_tis(bits: Sequence[int], *, weights: np.ndarray = DEFAULT_WEIGHTS) -> np.ndarray:
    if len(bits) != CHROMA_LEN:
        raise ChromaInputError(f"Expected {CHROMA_LEN} bits, got {len(bits)}.")
    arr = np.array(bits, dtype=np.float64)[None, :]
    return chroma_matrix_to_tis(arr, weights=weights)[0]


@dataclass(frozen=True)
class TISIndex:
    rep_names: np.ndarray  # (M,) dtype str; primary representative per unique chroma mask
    chroma_bits: np.ndarray  # (M,12) uint8; chroma for representative
    chroma_mask: np.ndarray  # (M,) uint16/uint32; unique chroma masks
    tis: np.ndarray  # (M,6) complex128; TIS for representative
    tis_norm: np.ndarray  # (M,) float64
    tis_unit: np.ndarray  # (M,6) complex128
    rep_offsets: np.ndarray  # (M+1,) int32; slice offsets into rep_names_by_root
    rep_names_by_root: np.ndarray  # (R,) dtype str; flattened per-root canonical reps
    alias_offsets: np.ndarray  # (M+1,) int32; slice offsets into alias_names
    alias_names: np.ndarray  # (K,) dtype str; flattened aliases (includes representative)
    meta: Mapping[str, object]

    def reps_for_row(self, row: int) -> list[str]:
        start = int(self.rep_offsets[row])
        end = int(self.rep_offsets[row + 1])
        return [str(x) for x in self.rep_names_by_root[start:end].tolist()]

    def aliases_for_row(self, row: int) -> list[str]:
        start = int(self.alias_offsets[row])
        end = int(self.alias_offsets[row + 1])
        return [str(x) for x in self.alias_names[start:end].tolist()]

    def build_name_to_row(self) -> dict[str, int]:
        name_to_row: dict[str, int] = {}
        for i in range(int(self.rep_names.shape[0])):
            for name in self.aliases_for_row(i):
                name_to_row[name] = i
        return name_to_row

    def build_mask_to_row(self) -> dict[int, int]:
        return {int(m): i for i, m in enumerate(self.chroma_mask.tolist())}

    def to_npz(self, path: Path) -> None:
        meta_json = json.dumps(dict(self.meta), ensure_ascii=False, sort_keys=True)
        np.savez_compressed(
            path,
            rep_names=self.rep_names,
            chroma_bits=self.chroma_bits,
            chroma_mask=self.chroma_mask,
            tis=self.tis,
            tis_norm=self.tis_norm,
            tis_unit=self.tis_unit,
            rep_offsets=self.rep_offsets,
            rep_names_by_root=self.rep_names_by_root,
            alias_offsets=self.alias_offsets,
            alias_names=self.alias_names,
            meta_json=np.array(meta_json),
        )

    @staticmethod
    def from_npz(path: Path) -> "TISIndex":
        with np.load(path, allow_pickle=False) as z:
            meta_json = str(z["meta_json"].tolist())
            meta = json.loads(meta_json)
            if "rep_names" in z:
                rep_offsets = z["rep_offsets"] if "rep_offsets" in z else None
                rep_names_by_root = z["rep_names_by_root"] if "rep_names_by_root" in z else None
                if rep_offsets is None or rep_names_by_root is None:
                    # Older deduped files without per-root reps: treat primary rep as the only rep.
                    m = int(z["rep_names"].shape[0])
                    rep_offsets = np.arange(0, m + 1, dtype=np.int32)
                    rep_names_by_root = z["rep_names"]
                return TISIndex(
                    rep_names=z["rep_names"],
                    chroma_bits=z["chroma_bits"],
                    chroma_mask=z["chroma_mask"],
                    tis=z["tis"],
                    tis_norm=z["tis_norm"],
                    tis_unit=z["tis_unit"],
                    rep_offsets=rep_offsets,
                    rep_names_by_root=rep_names_by_root,
                    alias_offsets=z["alias_offsets"],
                    alias_names=z["alias_names"],
                    meta=meta,
                )

            # Backward compatibility for older files that stored one row per chord name.
            names = z["names"]
            chroma_bits = z["chroma_bits"]
            chroma_mask = z["chroma_mask"]
            tis = z["tis"]
            tis_norm = z["tis_norm"]
            tis_unit = z["tis_unit"]
            n = int(names.shape[0])
            alias_offsets = np.arange(0, n + 1, dtype=np.int32)
            rep_offsets = np.arange(0, n + 1, dtype=np.int32)
            return TISIndex(
                rep_names=names,
                chroma_bits=chroma_bits,
                chroma_mask=chroma_mask,
                tis=tis,
                tis_norm=tis_norm,
                tis_unit=tis_unit,
                rep_offsets=rep_offsets,
                rep_names_by_root=names,
                alias_offsets=alias_offsets,
                alias_names=names,
                meta=meta,
            )


def build_tis_index(
    chords_to_bits: Mapping[str, Sequence[int]],
    *,
    weights: np.ndarray = DEFAULT_WEIGHTS,
    bit_order: np.ndarray = DEFAULT_BIT_ORDER,
    source_name: str = "guitar_chords_chroma.json",
) -> TISIndex:
    mask_to_aliases: dict[int, list[str]] = {}
    for chord_name, bits in chords_to_bits.items():
        mask = bits_to_mask(bits)
        mask_to_aliases.setdefault(mask, []).append(chord_name)

    masks = np.array(sorted(mask_to_aliases.keys()), dtype=np.uint16)
    rep_names_list: list[str] = []
    rep_bits_list: list[Sequence[int]] = []
    rep_offsets_list: list[int] = [0]
    flat_reps: list[str] = []
    alias_offsets_list: list[int] = [0]
    flat_aliases: list[str] = []

    for mask in masks.tolist():
        aliases = sorted(mask_to_aliases[int(mask)])
        reps_by_root = choose_representatives_by_root(aliases)
        rep = choose_representative(reps_by_root) if reps_by_root else choose_representative(aliases)
        rep_names_list.append(rep)
        rep_bits_list.append(chords_to_bits[rep])
        flat_reps.extend(reps_by_root if reps_by_root else [rep])
        rep_offsets_list.append(len(flat_reps))
        flat_aliases.extend(aliases)
        alias_offsets_list.append(len(flat_aliases))

    rep_names = np.array(rep_names_list, dtype="<U64")
    chroma_bits = np.array(rep_bits_list, dtype=np.uint8)
    rep_offsets = np.array(rep_offsets_list, dtype=np.int32)
    rep_names_by_root = np.array(flat_reps, dtype="<U64")
    alias_offsets = np.array(alias_offsets_list, dtype=np.int32)
    alias_names = np.array(flat_aliases, dtype="<U64")

    tis = chroma_matrix_to_tis(chroma_bits, weights=weights)
    tis_norm = np.sqrt(np.sum(np.abs(tis) ** 2, axis=1))
    tis_unit = tis / tis_norm[:, None]

    meta = {
        "source": source_name,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "chroma_len": CHROMA_LEN,
        "tis_dim": TIS_DIM,
        "bit_order": [str(x) for x in bit_order.tolist()],
        "weights": [float(x) for x in np.asarray(weights, dtype=np.float64).tolist()],
        "num_chords": int(len(chords_to_bits)),
        "num_vectors": int(rep_names.shape[0]),
    }
    return TISIndex(
        rep_names=rep_names,
        chroma_bits=chroma_bits,
        chroma_mask=masks,
        tis=tis,
        tis_norm=tis_norm.astype(np.float64, copy=False),
        tis_unit=tis_unit.astype(np.complex128, copy=False),
        rep_offsets=rep_offsets,
        rep_names_by_root=rep_names_by_root,
        alias_offsets=alias_offsets,
        alias_names=alias_names,
        meta=meta,
    )
