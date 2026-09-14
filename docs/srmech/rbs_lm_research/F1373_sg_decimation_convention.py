"""F1373 supporting measurement: which Sierpinski-gasket decimation polynomial
holds in which Laplacian convention.

Context. `256ba6b78` (research/sm-inverse-decimation-spike) rewrote the MFO
notebook's §IV.2 display equations from R(l) = l(5 - l) to R(l) = l(5 - 4l).
`main`'s MFO Part-I notice (rc459) declined to rewrite §IV.2 "on prose authority"
and named the unrun measurement: eigendecompose Sierpinski-gasket graphs
directly and read off where the two forms hold. This script runs it.

Method. Build the level-m pre-gasket graph G_m (m = 1..4) exactly, as integer
lattice coordinates. Form its combinatorial Laplacian D - A with
`srmech.math.laplacian.dense_laplacian` and take eigenvalues with
`srmech.math.laplacian.jacobi_eigvals` (float). Two boundary treatments:

  * DIRICHLET: rows/columns of the 3 corner vertices removed; every remaining
    vertex has degree 4.
  * FULL GRAPH: all vertices kept; the 3 corners have degree 2.

and two scalings of the same operator:

  * COMBINATORIAL  : eigenvalues of D - A as computed.
  * DEGREE-4-NORMALISED : the same eigenvalues divided by 4 (for the Dirichlet
    block this is exactly I - A/4, the probabilistic Laplacian, since every
    kept vertex has degree 4).

For every level-(m+1) eigenvalue l the test asks whether R(l) lies in the
level-m spectrum (float tolerance 1e-9). The exceptional ("born" / forbidden)
values of each convention are reported separately, not silently dropped.

No numpy. No abs(): distances go through `srmech.cascade.magnitude`.
"""
from __future__ import annotations

import sys

import srmech
from srmech.math.laplacian import dense_laplacian, jacobi_eigvals

try:
    from srmech.cascade import magnitude
except ImportError:  # pragma: no cover - older layout
    from srmech.cascade.atoms import magnitude  # type: ignore

TOL = 1e-9


def sg_graph(level: int):
    """Vertices (lattice coords) and undirected edges of the level-`level` SG graph."""
    size = 2 ** level
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    def rec(a: int, b: int, s: int) -> None:
        if s == 1:
            c = [(a, b), (a + 1, b), (a, b + 1)]
            for i in range(3):
                for j in range(i + 1, 3):
                    u, v = sorted((c[i], c[j]))
                    edges.add((u, v))
            return
        h = s // 2
        rec(a, b, h)
        rec(a + h, b, h)
        rec(a, b + h, h)

    rec(0, 0, size)
    verts = sorted({p for e in edges for p in e})
    corners = {(0, 0), (size, 0), (0, size)}
    return verts, sorted(edges), corners


def spectrum(level: int, dirichlet: bool) -> list[float]:
    verts, edges, corners = sg_graph(level)
    keep = [v for v in verts if not (dirichlet and v in corners)]
    idx = {v: i for i, v in enumerate(keep)}
    n = len(keep)
    if n == 0:
        return []
    # Dirichlet: an edge to a removed corner still counts toward the degree
    # (the corner value is pinned to 0), so build D - A over ALL vertices and
    # take the principal sub-block of the kept ones.
    all_idx = {v: i for i, v in enumerate(verts)}
    e_all = [(all_idx[u], all_idx[v]) for u, v in edges]
    L_full = dense_laplacian(len(verts), e_all)
    rows = [[L_full[all_idx[a]][all_idx[b]] for b in keep] for a in keep]
    ev = jacobi_eigvals(rows)
    return sorted(float(x) for x in ev)


def near(x: float, pool: list[float]) -> bool:
    return any(magnitude(x - p) <= TOL for p in pool)


def check(label: str, scale: float, poly, dirichlet: bool, exceptional: list[float]) -> dict:
    out = {"convention": label, "boundary": "dirichlet" if dirichlet else "full-graph", "levels": []}
    for m in (1, 2, 3):
        lo = [x / scale for x in spectrum(m, dirichlet)]
        hi = [x / scale for x in spectrum(m + 1, dirichlet)]
        hit = miss = exc = 0
        misses = []
        for lam in hi:
            if near(lam, exceptional):
                exc += 1
                continue
            if near(poly(lam), lo):
                hit += 1
            else:
                miss += 1
                misses.append(round(lam, 6))
        out["levels"].append({"m": m, "n_hi": len(hi), "mapped_into_level_m": hit,
                              "not_mapped": miss, "exceptional_skipped": exc,
                              "first_unmapped": misses[:4]})
    return out


def main() -> None:
    print("python", sys.version.split()[0], "| srmech", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT")
    except ImportError:
        print("numpy absent")
    for m in (1, 2):
        print(f"level {m} Dirichlet spectrum (combinatorial):",
              [round(x, 6) for x in spectrum(m, True)])
    r1 = lambda x: x * (5.0 - x)          # noqa: E731  R(l) = l(5 - l)
    r4 = lambda x: x * (5.0 - 4.0 * x)    # noqa: E731  R(l) = l(5 - 4l)
    exc_comb = [2.0, 5.0, 6.0]
    exc_norm = [0.5, 1.25, 1.5]
    rows = [
        check("combinatorial, R=l(5-l)", 1.0, r1, True, exc_comb),
        check("combinatorial, R=l(5-4l)", 1.0, r4, True, exc_comb),
        check("degree-4-normalised, R=l(5-4l)", 4.0, r4, True, exc_norm),
        check("degree-4-normalised, R=l(5-l)", 4.0, r1, True, exc_norm),
        check("combinatorial, R=l(5-l)", 1.0, r1, False, exc_comb),
        check("degree-4-normalised, R=l(5-4l)", 4.0, r4, False, exc_norm),
    ]
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
