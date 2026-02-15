from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..tis_index import angle, euclidean_distance


@dataclass
class Node:
    kind: str  # "TR" | "DR" | "SR" | "ROOT"
    start: int
    end: int
    head_pos: int
    left: "Node | None" = None

    parent: "Node | None" = None

    def set_children(self, left: "Node", right: "Node") -> None:
        self.left = left
        self.right = right
        left.parent = self
        right.parent = self


def harmonic_function_label_from_tis(tis: np.ndarray, protos: dict[str, np.ndarray]) -> str:
    """Map a chord TIS to paper function labels: t / s / d via min angle to I/IV/V."""
    best = None
    best_name = None
    for name, proto in protos.items():
        a = angle(tis, proto)
        if best is None or a < best:
            best = a
            best_name = name
    return {"tonic": "t", "subdominant": "s", "dominant": "d"}[str(best_name)]


def hierarchical_tension_last(
    *,
    tis_list: Sequence[np.ndarray],
    func_labels: Sequence[str],
    key_distances: Sequence[float],
) -> float:
    """Compute hierarchical tension h for the last chord (Eq. (9)).

    Deterministic heuristic for Section 3.6 tree construction (Rohrmeier-style).
    """
    n = len(tis_list)
    if n <= 1:
        return 0.0
    if len(func_labels) != n or len(key_distances) != n:
        raise ValueError("tis_list, func_labels, and key_distances must have equal length.")

    region = {"t": "TR", "s": "SR", "d": "DR"}
    nodes: list[Node] = []
    leaf_nodes: list[Node] = []
    for i, f in enumerate(func_labels):
        k = region.get(f)
        if k is None:
            raise ValueError(f"Unknown function label: {f!r}")
        node = Node(kind=k, start=i, end=i + 1, head_pos=i)
        nodes.append(node)
        leaf_nodes.append(node)

    def stable_head(a: int, b: int) -> int:
        prio = {"t": 0, "s": 1, "d": 2}
        ta = (prio.get(func_labels[a], 9), float(key_distances[a]))
        tb = (prio.get(func_labels[b], 9), float(key_distances[b]))
        return a if ta <= tb else b

    def merge(i: int, kind: str, head_pos: int) -> None:
        left = nodes[i]
        right = nodes[i + 1]
        new = Node(kind=kind, start=left.start, end=right.end, head_pos=head_pos)
        new.set_children(left, right)
        nodes[i : i + 2] = [new]

    changed = True
    while changed and len(nodes) > 1:
        changed = False
        for i in range(len(nodes) - 1):
            a, b = nodes[i], nodes[i + 1]
            if a.kind == "SR" and b.kind == "DR":
                merge(i, "DR", b.head_pos)
                changed = True
                break
        if changed:
            continue
        for i in range(len(nodes) - 1):
            a, b = nodes[i], nodes[i + 1]
            if a.kind == "DR" and b.kind == "TR":
                merge(i, "TR", b.head_pos)
                changed = True
                break
        if changed:
            continue
        for i in range(len(nodes) - 1):
            a, b = nodes[i], nodes[i + 1]
            if a.kind == "TR" and b.kind == "DR":
                merge(i, "TR", a.head_pos)
                changed = True
                break

    while len(nodes) > 1:
        a, b = nodes[0], nodes[1]
        head = stable_head(a.head_pos, b.head_pos)
        new = Node(kind="ROOT", start=a.start, end=b.end, head_pos=head)
        new.set_children(a, b)
        nodes[0:2] = [new]

    leaf = leaf_nodes[-1]
    current = leaf.parent
    parent_heads: list[int] = []
    while current is not None:
        hp = int(current.head_pos)
        if hp != n - 1:
            if not parent_heads or parent_heads[-1] != hp:
                parent_heads.append(hp)
        current = current.parent

    if not parent_heads:
        return 0.0

    ti = tis_list[-1]
    total = 0.0
    for hp in parent_heads:
        total += euclidean_distance(ti, tis_list[hp])
    return float(total / len(parent_heads))
