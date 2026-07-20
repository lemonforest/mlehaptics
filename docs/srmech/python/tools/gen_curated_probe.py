#!/usr/bin/env python3
"""Dev-time PROBE that executes the central ops with real inputs + captures
verified input->output, refreshing their _tool_docs_curated.py CURATED rows.

NOT the SSoT — the human reviews/edits the emitted file. This just guarantees
every curated EXAMPLE is a REAL executed result (never hand-typed / fabricated).
Run:  python tools/gen_curated_probe.py   (from docs/srmech/python)

**MERGES, never clobbers (rc291, #916).** This script used to write the whole
file from the ``CENTRAL`` list below, which silently deleted every curated
entry CENTRAL does not mention — the same "generator eats curation" defect
that #916 tracked in gen_tool_docs.py, but worse, because here the casualty
is the curation SSoT itself. It now loads the existing CURATED, updates only
the keys it actually probed, and reports preserved-vs-refreshed counts. A key
present on disk is never dropped.
"""
from __future__ import annotations
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import srmech  # noqa: F401,E402
from srmech.amsc.tool_schema import warmup_all  # noqa: E402
warmup_all()

_EDGES = [(0, 1), (1, 2), (2, 0), (2, 3)]
_W = [1.0, 1.0, 1.0, 1.0]


def _resolve(name):
    import importlib
    mod, _, attr = name.rpartition(".")
    return getattr(importlib.import_module(mod), attr)


_DL = _resolve("srmech.amsc.laplacian.dense_laplacian")(n=4, edges=_EDGES, weights=_W)

# (tool name, (args tuple, kwargs dict), curated explanation or None=use docstring)
CENTRAL = [
    ("srmech.amsc.laplacian.dense_laplacian", ((), dict(n=4, edges=_EDGES, weights=_W)),
     "Combinatorial graph Laplacian L = D − A of a weighted undirected graph "
     "(n nodes, edges + per-edge weights) as a dense Mat — the foundation the "
     "Class-L spectral readers (fiedler / spine / eigvals) run on. F1216: the "
     "Class-L Laplacian IS the LONG-TERM relational STORE (exact, addressed, "
     "directional, GROWS with knowledge — the genome / disk); the Class-M "
     "Klein-4/HDC bundle is the transient working-memory read, bridged by the "
     "reversible spectral basis-change (eigen / Walsh-Hadamard)."),
    ("srmech.amsc.laplacian.jacobi_eigvals", ((_DL,), {}),
     "Ascending eigenvalues of a symmetric Mat via cyclic Jacobi rotations "
     "(no numpy). On a graph Laplacian: λ0 = 0 for a connected graph; λ1 (the "
     "Fiedler value) measures algebraic connectivity."),
    ("srmech.amsc.laplacian.fiedler_vector", ((_DL,), {}),
     "Eigenvector of the second-smallest Laplacian eigenvalue (λ1). Its sign "
     "per node gives the natural 2-way spectral cut of the graph."),
    ("srmech.amsc.laplacian.three_fold_eigvec_groups", ((_DL,), {}),
     "3-way spectral partition from the sign pattern across the low eigenvectors "
     "(the k=3 community read; complements fiedler's 2-way and spine's centrality)."),
    ("srmech.amsc.laplacian.spectral_spine", ((), dict(edges=_EDGES, weights=_W, k=3)),
     "The structurally-central 'spine': top-|component| nodes of the dominant-"
     "eigenvalue eigenvector — the centrality axis, complementing the community "
     "readers (fiedler 2-way / three_fold 3-way)."),
    ("srmech.amsc.cascade.the_one", ((), dict(sigma=1, theta_num=1, theta_den=4, w=(1, 0, 1))),
     "The One S(σ,θ,w) = ⨁(ℝ·1 ⊕ σ·e^{Î·θ}·Im 𝔸ₙ) over the 1+3+7 Hurwitz tower "
     "(dim 2+4+8=14). σ is chirality, (θ_num/θ_den) the epicycle angle, and the "
     "winding triad w = (Saros, Metonic, Callippic) carries the spinor sign "
     "(−1)^Σw + the metacycle tower — the object whose two chiralities are one."),
    ("srmech.amsc.cyclic.gcd", ((), dict(a=12, b=18)), None),
    ("srmech.amsc.cyclic.mod_pow", ((), dict(a=7, k=13, n=11)),
     "Modular exponentiation a^k mod n by square-and-multiply (Class-I cyclic "
     "group). Exact; the Fermat/RSA-style fast power on ℤ/n."),
    ("srmech.amsc.rational.best_rational", ((), dict(numerator=314159, denominator=100000, max_denominator=100)),
     "Best rational p/q with q ≤ max_denominator approximating numerator/"
     "denominator (Class-N small-denominator anchor via continued fractions). "
     "Takes an INTEGER numerator/denominator pair, never a float."),
    ("srmech.amsc.primes.is_prime", ((), dict(n=97)),
     "Deterministic primality test (Class-J). True iff n is prime."),
    ("srmech.amsc.format.sha256_bytes", ((), dict(data=b"abc")), None),
    ("srmech.amsc.hdc.bind", ((), dict(a=b"abc", b=b"abc")),
     "Component-wise XOR of two binary-spatter-code (BSC) hypervectors — the "
     "Class-M bind that ties a role to a filler; self-inverse (bind(x,x)=0). "
     "F1216: Class-M / HDC = WORKING MEMORY / active context (fuzzy, composable, "
     "BOUNDED ~24-bind span, gracefully decays) — a transient read of the "
     "Class-L Laplacian long-term store, never the store itself."),
    ("srmech.amsc.hdc.bundle", ((), dict(vectors=[b"abc", b"abd", b"abe"])),
     "Majority-rule superposition of several BSC hypervectors into one that is "
     "similar to each input — the Class-M bundle (the set/record former)."),
    ("srmech.amsc.hdc.similarity", ((), dict(a=b"abc", b=b"abd")),
     "Normalised agreement (1 − 2·Hamming/D) between two BSC hypervectors, as an "
     "exact rational Q. +1 = identical, 0 = orthogonal, −1 = complementary."),
    ("srmech.amsc.cascade.magnitude", ((), dict(x=-3.5)),
     "The Class-K real pin-slot magnitude |x| — the cascade-honest replacement "
     "for Python abs(): a sign-branch phase-boundary op, NOT a complex modulus "
     "(it rejects complex input by contract)."),
    ("srmech.amsc.cascade.pin_slot_at_zero", ((), dict(x=-3.5)),
     "The Class-K pin-slot at zero: splits x into its sign (the pinned phase "
     "boundary, −1/0/+1) and its magnitude — the primitive |·| composes from."),
    ("srmech.amsc.cascade.net_chirality", ((), dict(orientations=[1, -1, 1, 1])),
     "Class-C net chirality: the signed product/sum reduction of a sequence of "
     "per-step orientations into the one net which-way handedness."),
]


def _rs(v):
    r = repr(v)
    return r if len(r) <= 200 else r[:197] + "..."


def merge_curated(existing, probed):
    """``existing`` curation with ``probed`` rows laid OVER it, per field.

    The whole point is what it does NOT do: no key in ``existing`` is ever
    dropped because ``probed`` (i.e. ``CENTRAL``) fails to mention it. That
    wholesale-rebuild was the rc291 #916 defect on this side.
    """
    merged = {k: dict(v) for k, v in existing.items()}
    for name, entry in probed.items():
        merged.setdefault(name, {}).update(entry)
    return merged


def main():
    out = {}
    for name, (args, kwargs), expl in CENTRAL:
        try:
            fn = _resolve(name)
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                res = fn(*args, **kwargs)
            inp = {f"arg{i}": _rs(a) for i, a in enumerate(args)}
            inp.update({k: _rs(v) for k, v in kwargs.items()})
            entry = {}
            if expl:
                entry["explanation"] = expl
            entry["example"] = {"input": inp, "output": _rs(res)}
            out[name] = entry
            print(f"OK  {name}  -> {_rs(res)[:60]}")
        except Exception as e:  # noqa: BLE001
            print(f"SKIP {name}: {type(e).__name__}: {e}")
    import json
    # MERGE over the existing curation — never rebuild the file from CENTRAL
    # alone (rc291 #916). CENTRAL is a probe list, not the curation SSoT: most
    # curated entries (the genome / plasmid / text explanations) are not in it
    # and a wholesale rewrite would delete every one of them.
    try:
        from srmech.amsc._tool_docs_curated import CURATED as _existing
    except Exception:  # noqa: BLE001 — first run / syntactically broken file
        _existing = {}
    merged = merge_curated(_existing, out)
    preserved = sorted(set(merged) - set(out))

    lines = ['"""_tool_docs_curated.py — HAND-CURATED introspection docs for the',
             "central ops (rc240 #838). Merged OVER the docstring-seeded floor by",
             "tools/gen_tool_docs.py (curation wins). Every EXAMPLE here is a REAL",
             "executed result (probed by tools/gen_curated_probe.py), never typed.",
             "",
             "THIS is the file to hand-edit. ``_tool_docs.py`` is GENERATED —",
             "text written there is destroyed by the next tools/gen_tool_docs.py",
             "run, which is what happened to the genome/plasmid explanations",
             "between rc274 and rc290 (rc291 migrated them here). The generator",
             "now refuses to write when it would clobber prose it cannot",
             're-derive from a docstring, so that failure mode is loud."""',
             "from __future__ import annotations", "",
             "from typing import Any, Dict", "",
             "CURATED: Dict[str, Dict[str, Any]] = {"]
    for name in sorted(merged):
        lines.append(f"    {json.dumps(name)}: "
                     f"{json.dumps(merged[name], sort_keys=True, ensure_ascii=False)},")
    lines.append("}")
    lines.append("")
    dest = Path(__file__).resolve().parent.parent / "srmech" / "amsc" / "_tool_docs_curated.py"
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"\nwrote {dest} — {len(merged)} curated entries "
          f"({len(out)} refreshed by this probe, {len(preserved)} preserved)")


if __name__ == "__main__":
    main()
