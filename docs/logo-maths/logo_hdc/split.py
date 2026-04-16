"""SplitObject — two HDC subspaces coupled by an explicit fiber.

A SplitObject holds:

    left  : codebook for the "left" subspace   (dict: name → HD)
    right : codebook for the "right" subspace  (dict: name → HD)
    M     : fiber matrix ∈ ℝ^{|left| × |right|} — coupling weights
    F     : fiber HV — the same coupling expressed as a single
            high-dim vector, supporting noisy associative retrieval

Invariant: M and F carry the same information; they are two views of
the fiber. Built together by `fiber.build_fiber_matrix` +
`fiber.fiber_to_hdc`.

Independent inferability:
    - You can probe the left subspace by asking:
        for name, hv in sp.left.items(): sim(probe, hv)
      without touching F or M.
    - Same for right.
    - You only need F (or M) when you want *coupling* information.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .hd import HD


@dataclass
class SplitObject:
    name: str
    left: Dict[str, HD]
    right: Dict[str, HD]
    left_order: List[str]      # canonical ordering (fiber matrix rows)
    right_order: List[str]     # canonical ordering (fiber matrix cols)
    M: Optional[np.ndarray] = None      # fiber matrix, built on demand
    F: Optional[HD] = None              # fiber HV, built on demand

    def left_hv(self, name: str) -> HD:
        return self.left[name]

    def right_hv(self, name: str) -> HD:
        return self.right[name]

    def shape(self) -> tuple[int, int]:
        return (len(self.left_order), len(self.right_order))
