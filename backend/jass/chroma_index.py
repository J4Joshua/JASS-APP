from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


CHROMA_LEN = 12


class ChromaInputError(ValueError):
    pass


def chord_root(name: str) -> str:
    """
    Extract the chord root pitch class from a chord name.
    Expected formats start with [A-G] optionally followed by '#' or 'b'.
    Examples: 'C', 'C#maj7', 'A#7#9', 'C/E' -> roots 'C', 'C#', 'A#', 'C'.
    """
    if not name:
        return ""
    c0 = name[0].upper()
    if c0 < "A" or c0 > "G":
        return ""
    if len(name) >= 2 and name[1] in ("#", "b"):
        return c0 + name[1]
    return c0


def _name_pref_key(name: str) -> tuple[int, int, str]:
    # Prefer root-position spellings if available, then shorter, then lexicographic for stability.
    return (1 if "/" in name else 0, len(name), name)


def choose_shortest_no_slash(names: Sequence[str]) -> str:
    """
    Prefer a name without '/', but if all have '/', return the shortest (then lexicographic).
    """
    if not names:
        raise ValueError("choose_shortest_no_slash requires a non-empty list.")
    no_slash = [n for n in names if "/" not in n]
    pool = no_slash if no_slash else list(names)
    return min(pool, key=lambda n: (len(n), n))


def filter_slash_suggestions(names: Sequence[str]) -> list[str]:
    """
    Filter out chord names containing '/' for display.
    If that would remove everything, keep only the shortest one.
    """
    names_list = [n for n in names if isinstance(n, str)]
    no_slash = [n for n in names_list if "/" not in n]
    if no_slash:
        return no_slash
    if not names_list:
        return []
    shortest = min(names_list, key=lambda n: (len(n), n))
    return [shortest]


def choose_representative(chord_names: Sequence[str]) -> str:
    """
    Pick a stable, human-friendly representative chord name for a set of aliases
    that share the same chroma vector.

    Heuristic: prefer non-inversion names (no '/'), then shorter names, then
    lexicographic order for stability.
    """
    if not chord_names:
        raise ValueError("choose_representative requires a non-empty list.")

    return min(chord_names, key=_name_pref_key)


def choose_representatives_by_root(chord_names: Sequence[str]) -> list[str]:
    """
    Choose one canonical name per root pitch class.
    For each root, pick the "simplest" (shortest, preferably no inversion) name.
    """
    if not chord_names:
        return []

    by_root: dict[str, list[str]] = {}
    for name in chord_names:
        r = chord_root(name)
        if not r:
            continue
        by_root.setdefault(r, []).append(name)

    reps: list[str] = []
    for r, names in by_root.items():
        reps.append(choose_shortest_no_slash(names))

    reps.sort(key=_name_pref_key)
    return reps


def bits_to_mask(bits: Sequence[int]) -> int:
    if len(bits) != CHROMA_LEN:
        raise ChromaInputError(f"Expected {CHROMA_LEN} bits, got {len(bits)}.")
    mask = 0
    for i, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ChromaInputError(f"Bits must be 0/1; got {bit!r} at index {i}.")
        if bit:
            mask |= 1 << i
    return mask


def mask_to_bits(mask: int) -> list[int]:
    if mask < 0 or mask >= (1 << CHROMA_LEN):
        raise ChromaInputError(f"Mask must be in [0, {1<<CHROMA_LEN}); got {mask}.")
    return [(mask >> i) & 1 for i in range(CHROMA_LEN)]


def bits_to_bitstring(bits: Sequence[int]) -> str:
    if len(bits) != CHROMA_LEN:
        raise ChromaInputError(f"Expected {CHROMA_LEN} bits, got {len(bits)}.")
    return "".join("1" if int(b) else "0" for b in bits)


def mask_to_bitstring(mask: int) -> str:
    return bits_to_bitstring(mask_to_bits(mask))


def bitstring_to_mask(bitstring: str) -> int:
    s = bitstring.strip()
    if len(s) != CHROMA_LEN or any(c not in "01" for c in s):
        raise ChromaInputError(f"Expected {CHROMA_LEN}-char 0/1 bitstring; got {bitstring!r}.")
    return bits_to_mask([int(c) for c in s])


_NOTE_NAMES_SHARP_LOWER = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
_NOTE_NAMES_FLAT_LOWER = ["c", "db", "d", "eb", "e", "f", "gb", "g", "ab", "a", "bb", "b"]


def chroma_bits_to_notes(bits: Sequence[int], *, flats: bool = False) -> list[str]:
    """
    Convert a 12-D chroma binary vector into note names (lowercase).
    Bit order matches the repo: [C, C#, D, D#, E, F, F#, G, G#, A, A#, B].
    """
    if len(bits) != CHROMA_LEN:
        raise ChromaInputError(f"Expected {CHROMA_LEN} bits, got {len(bits)}.")
    names = _NOTE_NAMES_FLAT_LOWER if flats else _NOTE_NAMES_SHARP_LOWER
    out: list[str] = []
    for i, b in enumerate(bits):
        if int(b) == 1:
            out.append(names[i])
    return out


def _parse_bits_list(value: object) -> list[int]:
    if not isinstance(value, list):
        raise ChromaInputError("Expected a JSON array of 12 integers (0/1).")
    bits: list[int] = []
    for i, v in enumerate(value):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ChromaInputError(f"Bit {i} must be an int 0/1; got {v!r}.")
        bits.append(v)
    if len(bits) != CHROMA_LEN:
        raise ChromaInputError(f"Expected {CHROMA_LEN} bits, got {len(bits)}.")
    for i, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ChromaInputError(f"Bits must be 0/1; got {bit!r} at index {i}.")
    return bits


def parse_chroma(text: str) -> list[int]:
    """
    Accepts:
      - "100010010000" (12 chars of 0/1)
      - "1,0,0,0,1,0,0,1,0,0,0,0"
      - "[1,0,0,0,1,0,0,1,0,0,0,0]" (JSON array)
    Returns: list[int] length 12.
    """
    s = text.strip()
    if len(s) == CHROMA_LEN and all(c in "01" for c in s):
        return [int(c) for c in s]

    if "," in s and all(c in "01, \t" for c in s):
        parts = [p.strip() for p in s.split(",")]
        if len(parts) != CHROMA_LEN:
            raise ChromaInputError(f"Expected {CHROMA_LEN} comma-separated bits, got {len(parts)}.")
        try:
            bits = [int(p) for p in parts]
        except ValueError as e:
            raise ChromaInputError("Comma-separated chroma must contain only 0/1.") from e
        return _parse_bits_list(bits)

    if s.startswith("["):
        try:
            value = json.loads(s)
        except json.JSONDecodeError as e:
            raise ChromaInputError("Invalid JSON array for chroma input.") from e
        return _parse_bits_list(value)

    raise ChromaInputError(
        "Unrecognized chroma format. Provide 12 bits like '100010010000' or "
        "'1,0,0,0,1,0,0,1,0,0,0,0' or a JSON array."
    )


def load_chords_chroma(path: Path) -> dict[str, list[int]]:
    """
    Loads the repo's source JSON format:
      { "C": [ { "chroma_binary": [0/1 x12] } ], ... }
    Returns:
      { "C": [0/1 x12], ... }
    """
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("Expected top-level JSON object.")

    out: dict[str, list[int]] = {}
    for chord_name, entries in raw.items():
        if not isinstance(chord_name, str):
            raise ValueError(f"Chord name must be string; got {type(chord_name).__name__}.")
        if not isinstance(entries, list) or len(entries) != 1:
            raise ValueError(f"Chord {chord_name!r} must map to a 1-item list.")
        entry = entries[0]
        if not isinstance(entry, dict) or "chroma_binary" not in entry:
            raise ValueError(f"Chord {chord_name!r} entry must contain 'chroma_binary'.")
        bits = _parse_bits_list(entry["chroma_binary"])
        out[chord_name] = bits
    return out


def build_chroma_index(chords_to_bits: Mapping[str, Sequence[int]]) -> dict[int, list[str]]:
    """
    Inverted index: mask -> [chord_name, ...]
    """
    index: dict[int, list[str]] = {}
    for chord_name, bits in chords_to_bits.items():
        mask = bits_to_mask(bits)
        index.setdefault(mask, []).append(chord_name)
    for chord_names in index.values():
        chord_names.sort()
    return dict(sorted(index.items(), key=lambda kv: kv[0]))


@dataclass(frozen=True)
class ChromaIndexFile:
    meta: dict[str, object]
    reps: dict[int, list[str]]
    aliases: dict[int, list[str]] | None = None

    def _key_format(self) -> str:
        key = str(self.meta.get("key", "mask12"))
        if key not in ("mask12", "bits12"):
            return "mask12"
        return key

    def to_json_obj(self) -> dict[str, object]:
        key_format = self._key_format()
        def encode_key(mask: int) -> str:
            return str(mask) if key_format == "mask12" else mask_to_bitstring(mask)

        obj: dict[str, object] = {
            "_meta": self.meta,
            "reps": {encode_key(k): v for k, v in self.reps.items()},
        }
        if self.aliases is not None:
            obj["aliases"] = {encode_key(k): v for k, v in self.aliases.items()}
        return obj

    @staticmethod
    def from_json_obj(obj: Mapping[str, object]) -> "ChromaIndexFile":
        if not isinstance(obj, Mapping):
            raise ValueError("Expected JSON object.")
        meta = obj.get("_meta")
        reps_obj = obj.get("reps")
        rep_index_obj = obj.get("rep_index")  # legacy single representative string
        aliases_obj = obj.get("aliases")
        legacy_index_obj = obj.get("index")
        if not isinstance(meta, dict):
            raise ValueError("Expected '_meta' object.")

        reps: dict[int, list[str]] = {}
        aliases: dict[int, list[str]] | None = None

        def parse_key(k: str) -> int:
            if isinstance(k, str) and len(k) == CHROMA_LEN and all(c in "01" for c in k):
                return bitstring_to_mask(k)
            return int(k)

        if isinstance(reps_obj, dict):
            for k, v in reps_obj.items():
                try:
                    mask = parse_key(str(k))
                except Exception as e:
                    raise ValueError(f"Invalid reps key {k!r}.") from e
                if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
                    raise ValueError(f"reps value for key {k!r} must be a list of strings.")
                reps[mask] = list(v)
        elif isinstance(rep_index_obj, dict):
            for k, v in rep_index_obj.items():
                try:
                    mask = parse_key(str(k))
                except Exception as e:
                    raise ValueError(f"Invalid rep_index key {k!r}.") from e
                if not isinstance(v, str):
                    raise ValueError(f"rep_index value for key {k!r} must be a string.")
                reps[mask] = [v]
        elif isinstance(legacy_index_obj, dict):
            # Backward compatibility: {"index": {mask: [names...]}}
            parsed_aliases: dict[int, list[str]] = {}
            for k, v in legacy_index_obj.items():
                try:
                    mask = parse_key(str(k))
                except Exception as e:
                    raise ValueError(f"Invalid index key {k!r}.") from e
                if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
                    raise ValueError(f"Index value for key {k!r} must be a list of strings.")
                names = list(v)
                names.sort()
                parsed_aliases[mask] = names
                reps[mask] = choose_representatives_by_root(names) or [choose_representative(names)]
            aliases = parsed_aliases
        else:
            raise ValueError("Expected 'reps' object (or legacy 'rep_index' / 'index').")

        if isinstance(aliases_obj, dict):
            parsed_aliases2: dict[int, list[str]] = {}
            for k, v in aliases_obj.items():
                try:
                    mask = parse_key(str(k))
                except Exception as e:
                    raise ValueError(
                        f"Invalid aliases key {k!r}."
                    ) from e
                if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
                    raise ValueError(f"aliases value for key {k!r} must be a list of strings.")
                parsed_aliases2[mask] = list(v)
            aliases = parsed_aliases2

        return ChromaIndexFile(meta=meta, reps=reps, aliases=aliases)


def make_index_file(source_path: Path, chords_to_bits: Mapping[str, Sequence[int]]) -> ChromaIndexFile:
    index = build_chroma_index(chords_to_bits)
    reps = {
        mask: filter_slash_suggestions(
            choose_representatives_by_root(names) or [choose_representative(names)]
        )
        for mask, names in index.items()
    }
    meta = {
        "source": str(source_path.name),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "chroma_len": CHROMA_LEN,
        "key": "mask12",
        "bit_order": [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ],
        "unique_keys": len(index),
        "num_chords": len(chords_to_bits),
    }
    return ChromaIndexFile(meta=meta, reps=reps, aliases=index)


def dump_index_file(path: Path, index_file: ChromaIndexFile) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(index_file.to_json_obj(), f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def load_index_file(path: Path) -> ChromaIndexFile:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    return ChromaIndexFile.from_json_obj(obj)
