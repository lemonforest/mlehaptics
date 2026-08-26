#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Directed / signed (non-Hermitian) Laplacian eigen-op SCAFFOLD.

STATUS: SCAFFOLD (gated). This harness is written *ahead of* a srmech
Class-L directed/non-Hermitian eigen-op that does not yet exist in
v0.6.0rc15. It is the executable target spec the future op must satisfy.

WHAT THIS IS FOR
----------------
The one-way circulation object (a directed n-cycle: 0->1->2->...->n-1->0)
has a Laplacian ``L = I - P`` where ``P`` is the cyclic-shift permutation
(out-degree exactly 1 per node, NOT symmetrized). Its eigenvalues are the
roots of unity translated onto the unit circle centred at +1:

    lambda_k = 1 - exp(2*pi*i*k/n),   k = 0..n-1,      all on |lambda - 1| = 1.

This complex spectrum on the circle |lambda-1|=1 IS the *circulation
signature* (Class C cascade-orientation / chirality made spectral): the
imaginary parts encode the one-way flow direction. A symmetric (Hermitian)
treatment cannot carry it — there is no chirality coordinate in a real
symmetric spectrum.

THE GAP (framework-reading only; this is NOT a srmech bug report)
-----------------------------------------------------------------
srmech v0.6.0rc15 ships ``srmech.amsc.laplacian`` whose builders
(``dense_laplacian`` / ``dense_adjacency``) *silently symmetrize* a directed
edge list, and whose eigen-ops (``jacobi_eigvals`` / ``symmetric_eigendecompose``
/ ``hermitian_eigendecompose``) are real-symmetric / Hermitian ONLY. Feeding
a directed n-cycle therefore collapses it to the *undirected* cycle and
returns a real-diameter spectrum (e.g. n=6 -> {0,1,1,3,3,4} from the
normalized/combinatorial undirected cycle) — the circulation signature is
destroyed, NOT merely approximated. So rc15 has NO op that yields the
circle-spectrum above. That absence is a known Class-L rework gap; the
triality op that would naturally host a directed treatment is also not in
rc15.

This scaffold therefore:
  (1) SWEEPS the live rc15 symbol surface to *confirm* no directed /
      non-Hermitian eigen-op exists (and that the builders symmetrize),
  (2) ENCODES the target: directed n-cycle L must yield lambda_k on
      |lambda-1|=1 as a SET (the circulation signature), distinct from the
      symmetric real projection rc15 actually gives,
  (3) defines PASS / SKIP / FAIL criteria + what a NULL looks like,
  (4) provides a ``numpy.linalg.eigvals`` REFERENCE ORACLE, *explicitly
      flagged as DIAGNOSTIC ONLY* — srmech has no directed eigen-op, so the
      oracle is the yardstick the future srmech op must match, never a
      stand-in we ship as a srmech result.

GATING
------
The PASS-bearing leg (CHECK 4) is GATED on a srmech directed eigen-op being
discoverable. Until one exists it reports SKIP (not FAIL): the target is
correct and the oracle confirms it, but the thing-under-test is absent.

NO-MAGIC ATTESTATION of the constants used here
-----------------------------------------------
  * n (cycle sizes 3,4,6,8) ...... B: chosen test sizes; small enough for
                                   exact eyeballing, >2 to expose complex pairs.
  * lambda_k = 1 - exp(2*pi*i*k/n)  A: attested-to-structure — the eigenvalues
                                   of the circulant shift P (P is the regular
                                   representation of the cyclic group Z_n;
                                   its eigenvalues are the n-th roots of unity
                                   e^{2 pi i k / n}; L = I - P shifts them).
                                   Class I (cyclic) x Class L (Laplacian).
  * |lambda - 1| = 1 ............. A: structural consequence — |exp(...)| = 1.
  * TOL = 1e-9 .................. B: numerical-equality floor for float64
                                   eigensolver agreement (well above the
                                   ~1e-12 jacobi tolerance, below signal).
  * chance / similarity etc. ..... not used here (no HDC leg).

DISCIPLINE: framework-reading only; never abs() inside a cascade (the
magnitude here is the Class-K/Class-L spectral modulus |lambda-1|, computed
on complex eigenvalues as a *diagnostic measurement of the oracle*, not a
cascade sign-fold); no CAD/fabrication; honest SKIP/NULL reporting; do not
file srmech issues. Run as:

    cd /tmp && /tmp/srmech_rc15_venv/bin/python \
        /abs/path/to/directed_laplacian_eigen_scaffold.py
"""

from __future__ import annotations

import json
import math
import sys
from typing import Optional

import numpy as np

# --------------------------------------------------------------------------
# Constants (attested above; A = structure-cascade, B = chosen floor/seed).
# --------------------------------------------------------------------------
CYCLE_SIZES = (3, 4, 6, 8)          # B: test sizes
TOL = 1e-9                          # B: float64 eigensolver agreement floor
CIRCLE_CENTER = 1.0                 # A: L = I - P  =>  spectrum centred at +1
CIRCLE_RADIUS = 1.0                 # A: |exp(2 pi i k/n)| = 1

results: dict[str, object] = {
    "scaffold": "directed_laplacian_eigen_scaffold",
    "srmech_version": None,
    "honest_status": "SCAFFOLD",
    "checks": [],
    "counts": {"PASS": 0, "SKIP": 0, "FAIL": 0, "NULL": 0},
}


def _record(name: str, verdict: str, detail: str, extra: Optional[dict] = None) -> None:
    """Log one check; verdict in {PASS, SKIP, FAIL, NULL}."""
    entry = {"check": name, "verdict": verdict, "detail": detail}
    if extra:
        entry.update(extra)
    results["checks"].append(entry)
    results["counts"][verdict] = results["counts"].get(verdict, 0) + 1
    print(f"[{verdict:4s}] {name}: {detail}")


# --------------------------------------------------------------------------
# Target spec (closed form) + reference oracle.
# --------------------------------------------------------------------------
def target_directed_cycle_spectrum(n: int) -> np.ndarray:
    """Closed-form circulation signature: lambda_k = 1 - exp(2 pi i k/n).

    Attested-to-structure (Class I cyclic-group regular rep x Class L).
    Returned as an UNORDERED set of complex eigenvalues.
    """
    ks = np.arange(n)
    return CIRCLE_CENTER - np.exp(2j * np.pi * ks / n)


def directed_cycle_laplacian(n: int) -> np.ndarray:
    """Directed n-cycle Laplacian L = I - P (out-degree 1, NOT symmetrized).

    P is the cyclic-shift permutation: P[i, (i+1) mod n] = 1.
    This is the matrix a directed/non-Hermitian srmech eigen-op MUST accept.
    """
    P = np.zeros((n, n), dtype=float)
    for i in range(n):
        P[i, (i + 1) % n] = 1.0
    return np.eye(n) - P


def reference_oracle_eigvals(matrix: np.ndarray) -> np.ndarray:
    """DIAGNOSTIC ONLY -- numpy.linalg.eigvals as the non-Hermitian yardstick.

    *** NOT a srmech result. *** srmech v0.6.0rc15 has NO directed /
    non-Hermitian eigen-op (known Class-L rework gap). This oracle exists
    solely so the future srmech op has a numerical target to match. Any
    value it returns must be labelled 'numpy-diagnostic', never attested as
    a srmech cascade output.
    """
    return np.linalg.eigvals(matrix)


def _sorted_complex(vals: np.ndarray) -> np.ndarray:
    """Canonical ordering of a complex spectrum for set-comparison."""
    return np.array(sorted(vals, key=lambda z: (round(z.real, 9), round(z.imag, 9))))


def spectra_match_as_set(a: np.ndarray, b: np.ndarray, tol: float = TOL) -> bool:
    """True iff a and b are the same multiset of complex numbers within tol."""
    if len(a) != len(b):
        return False
    return bool(np.allclose(_sorted_complex(a), _sorted_complex(b), atol=tol))


# --------------------------------------------------------------------------
# CHECK 1 -- confirm rc15 has NO directed / non-Hermitian eigen-op.
# --------------------------------------------------------------------------
def check1_no_directed_eigen_op() -> None:
    """Sweep srmech.amsc.laplacian + signal_processing for any directed op.

    PASS  : no directed/non-Hermitian eigen-op found AND builders symmetrize
            (confirms the gap is real -> the rest of the scaffold is warranted).
    FAIL  : a directed op IS present (the gap is closed -> CHECK 4 should run;
            update the scaffold's gating).
    NULL  : import failure / unexpected surface (cannot assess).
    """
    try:
        import srmech
        import srmech.amsc.laplacian as lap
        import srmech.signal_processing as sp
    except Exception as exc:  # noqa: BLE001
        _record("1_no_directed_eigen_op", "NULL",
                f"import failure: {exc!r}")
        return

    results["srmech_version"] = getattr(srmech, "__version__", "unknown")

    lap_syms = [s for s in dir(lap) if not s.startswith("_")]
    sp_syms = [s for s in dir(sp) if not s.startswith("_")]

    # Token-set that would signal a directed / non-Hermitian / complex eigen-op.
    directed_tokens = (
        "directed", "nonhermitian", "non_hermitian", "asymmetric",
        "signed_laplacian", "complex_eig", "general_eig", "eigvals_general",
        "schur", "triality", "magnetic_laplacian",
    )

    def _is_directed(name: str) -> bool:
        low = name.lower()
        return any(tok in low for tok in directed_tokens)

    found_directed = sorted(
        {s for s in lap_syms if _is_directed(s)}
        | {s for s in sp_syms if _is_directed(s)}
    )

    # Enumerate the eigen-ops that DO exist and confirm each is Hermitian-only.
    known_hermitian_only = [
        s for s in lap_syms
        if any(t in s.lower() for t in ("eig", "eigvals", "eigendecompose"))
    ]

    # Confirm the builders symmetrize a directed edge list (the silent collapse).
    symmetrizes = None
    try:
        n = 4
        directed_edges = [(i, (i + 1) % n) for i in range(n)]  # one-way ring
        A = lap.dense_adjacency(n, directed_edges)
        symmetrizes = bool(np.allclose(A, A.T))
    except Exception as exc:  # noqa: BLE001
        symmetrizes = f"could-not-build: {exc!r}"

    extra = {
        "laplacian_eigen_ops_present": known_hermitian_only,
        "directed_ops_found": found_directed,
        "dense_adjacency_symmetrizes_directed_edges": symmetrizes,
    }

    if found_directed:
        _record("1_no_directed_eigen_op", "FAIL",
                f"directed/non-Hermitian op(s) appeared: {found_directed} "
                f"-- gap may be closed; re-gate CHECK 4", extra)
    elif symmetrizes is True:
        _record("1_no_directed_eigen_op", "PASS",
                "no directed/non-Hermitian eigen-op in rc15; builders "
                "symmetrize directed edges (gap confirmed -- scaffold warranted)",
                extra)
    else:
        _record("1_no_directed_eigen_op", "NULL",
                f"no directed op found but symmetrization probe inconclusive "
                f"({symmetrizes!r})", extra)


# --------------------------------------------------------------------------
# CHECK 2 -- target spec: circulation signature on |lambda-1|=1.
# --------------------------------------------------------------------------
def check2_target_on_circle() -> None:
    """The closed-form target must lie on |lambda-1|=1 and be genuinely complex.

    PASS : for every n, all lambda_k satisfy |lambda_k - 1| == 1 (within tol)
           AND at least one eigenvalue has non-trivial imaginary part
           (i.e. the signature is NOT real-diameter-collapsible).
    FAIL : target falls off the circle, or is purely real for n>2.
    """
    all_on_circle = True
    all_have_imag = True
    per_n = {}
    for n in CYCLE_SIZES:
        spec = target_directed_cycle_spectrum(n)
        # modulus of (lambda - center): spectral magnitude, a diagnostic
        # measurement on complex numbers -- NOT a cascade sign-fold abs().
        radii = np.abs(spec - CIRCLE_CENTER)
        on_circle = bool(np.allclose(radii, CIRCLE_RADIUS, atol=TOL))
        max_imag = float(np.max(np.abs(spec.imag)))
        has_imag = max_imag > TOL  # n>2 should have a complex conjugate pair
        per_n[n] = {"on_circle": on_circle, "max_abs_imag": max_imag}
        all_on_circle = all_on_circle and on_circle
        if n > 2:
            all_have_imag = all_have_imag and has_imag

    if all_on_circle and all_have_imag:
        _record("2_target_on_circle", "PASS",
                "closed-form circulation signature lies on |lambda-1|=1 with "
                "non-trivial imaginary parts for n>2", {"per_n": per_n})
    else:
        _record("2_target_on_circle", "FAIL",
                f"target spec malformed (on_circle={all_on_circle}, "
                f"has_imag={all_have_imag})", {"per_n": per_n})


# --------------------------------------------------------------------------
# CHECK 3 -- contrast: rc15 symmetric projection is NOT the signature.
# --------------------------------------------------------------------------
def check3_symmetric_projection_differs() -> None:
    """Show srmech's Hermitian path gives a real spectrum != the signature.

    This is the *positive evidence* the gap matters: the answer rc15 returns
    today is real (no imaginary circulation part) and differs as a set from
    the directed target.

    PASS : srmech symmetric spectrum is all-real AND differs from the
           directed target set for every n>2.
    NULL : srmech eigen path unavailable.
    FAIL : (unexpected) srmech symmetric path already reproduces the
           complex signature -- would mean the gap is silently closed.
    """
    try:
        from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals
    except Exception as exc:  # noqa: BLE001
        _record("3_symmetric_projection_differs", "NULL",
                f"srmech eigen path unavailable: {exc!r}")
        return

    per_n = {}
    all_real = True
    all_differ = True
    for n in CYCLE_SIZES:
        directed_edges = [(i, (i + 1) % n) for i in range(n)]
        Lsym = dense_laplacian(n, directed_edges)          # silently symmetrized
        sym_spec = np.asarray(jacobi_eigvals(Lsym), dtype=complex)
        target = target_directed_cycle_spectrum(n)
        is_real = bool(np.allclose(sym_spec.imag, 0.0, atol=TOL))
        differs = not spectra_match_as_set(sym_spec, target)
        per_n[n] = {
            "srmech_symmetric_spectrum": [round(float(x.real), 6) for x in
                                          _sorted_complex(sym_spec)],
            "is_all_real": is_real,
            "differs_from_directed_target": differs,
        }
        all_real = all_real and is_real
        if n > 2:
            all_differ = all_differ and differs

    if all_real and all_differ:
        _record("3_symmetric_projection_differs", "PASS",
                "rc15 Hermitian path returns an all-real spectrum that differs "
                "(as a set) from the directed circulation signature -- gap is "
                "load-bearing", {"per_n": per_n})
    elif not all_real:
        _record("3_symmetric_projection_differs", "FAIL",
                "rc15 symmetric path returned complex values -- unexpected; "
                "re-examine", {"per_n": per_n})
    else:
        _record("3_symmetric_projection_differs", "FAIL",
                "rc15 symmetric spectrum already MATCHES the directed target "
                "-- gap appears closed; re-gate", {"per_n": per_n})


# --------------------------------------------------------------------------
# CHECK 4 -- GATED: the future srmech directed eigen-op must match the oracle.
# --------------------------------------------------------------------------
def _discover_srmech_directed_eigvals():
    """Return a callable srmech(matrix)->complex-spectrum if one exists, else None.

    Probes the live surface for a directed / non-Hermitian eigen-op. Returns
    None today (rc15) -> CHECK 4 SKIPs. When srmech adds the op, wire its name
    into the candidate list below and the gate opens automatically.
    """
    candidates = []
    try:
        import srmech.amsc.laplacian as lap
        candidates += [
            getattr(lap, nm, None) for nm in (
                "directed_eigvals", "nonhermitian_eigvals",
                "general_eigvals", "complex_eigvals",
                "signed_laplacian_eigvals", "magnetic_laplacian_eigvals",
            )
        ]
    except Exception:  # noqa: BLE001
        pass
    try:
        import srmech.signal_processing as sp
        candidates += [
            getattr(sp, nm, None) for nm in (
                "directed_eigvals", "triality_eigvals", "nonhermitian_eigvals",
            )
        ]
    except Exception:  # noqa: BLE001
        pass
    for c in candidates:
        if callable(c):
            return c
    return None


def check4_gated_op_matches_oracle() -> None:
    """The PASS-bearing leg. GATED on a srmech directed eigen-op existing.

    SKIP : no srmech directed eigen-op discoverable (the expected state on
           rc15). The reference oracle is still computed + reported so the
           target is anchored, but NOTHING-UNDER-TEST exists -> SKIP, not FAIL.
    PASS : srmech directed op exists AND its spectrum matches the closed-form
           target (and the diagnostic oracle) as a set, within tol, for all n.
    FAIL : srmech directed op exists but its spectrum does NOT match the target
           -> the implementation is wrong (this is the real regression catch).
    NULL : srmech op exists but raised / returned unusable output.

    WHAT A NULL LOOKS LIKE (documented for the operator): a NULL here means
    we found a callable but it threw, returned the wrong length, or returned
    NaN/inf -- i.e. we could not obtain a comparable spectrum at all. That is
    distinct from FAIL (a clean-but-wrong spectrum) and from SKIP (no op).
    """
    srmech_op = _discover_srmech_directed_eigvals()

    # Reference oracle (DIAGNOSTIC ONLY) -- anchor the target regardless.
    oracle_ok = True
    oracle_report = {}
    for n in CYCLE_SIZES:
        L = directed_cycle_laplacian(n)
        oracle_spec = reference_oracle_eigvals(L)          # numpy diagnostic
        target = target_directed_cycle_spectrum(n)
        match = spectra_match_as_set(oracle_spec, target)
        oracle_ok = oracle_ok and match
        oracle_report[n] = {
            "numpy_diagnostic_spectrum": [
                [round(float(z.real), 6), round(float(z.imag), 6)]
                for z in _sorted_complex(oracle_spec)
            ],
            "matches_closed_form_target": match,
            "source": "numpy.linalg.eigvals (DIAGNOSTIC ONLY -- "
                      "srmech has no directed eigen-op in rc15)",
        }

    if not oracle_ok:
        _record("4_gated_op_matches_oracle", "NULL",
                "reference oracle did NOT reproduce the closed-form target -- "
                "scaffold target/oracle inconsistent; fix before gating",
                {"oracle": oracle_report})
        return

    if srmech_op is None:
        _record("4_gated_op_matches_oracle", "SKIP",
                "no srmech directed/non-Hermitian eigen-op in rc15 (known "
                "Class-L rework gap). Oracle confirms the target; PASS leg is "
                "GATED until the op ships. Wire its name into "
                "_discover_srmech_directed_eigvals() to open the gate.",
                {"oracle": oracle_report,
                 "srmech_op_discovered": False})
        return

    # --- op exists: this branch runs only AFTER srmech adds the op ---
    per_n = {}
    all_match = True
    try:
        for n in CYCLE_SIZES:
            L = directed_cycle_laplacian(n)
            srmech_spec = np.asarray(srmech_op(L), dtype=complex)
            target = target_directed_cycle_spectrum(n)
            if len(srmech_spec) != n or not np.all(np.isfinite(srmech_spec)):
                _record("4_gated_op_matches_oracle", "NULL",
                        f"srmech op returned unusable spectrum for n={n} "
                        f"(len/finite check failed)",
                        {"oracle": oracle_report})
                return
            match = spectra_match_as_set(srmech_spec, target)
            per_n[n] = {
                "srmech_spectrum": [[round(float(z.real), 6),
                                     round(float(z.imag), 6)]
                                    for z in _sorted_complex(srmech_spec)],
                "matches_target": match,
            }
            all_match = all_match and match
    except Exception as exc:  # noqa: BLE001
        _record("4_gated_op_matches_oracle", "NULL",
                f"srmech directed op raised: {exc!r}",
                {"oracle": oracle_report})
        return

    if all_match:
        _record("4_gated_op_matches_oracle", "PASS",
                "srmech directed eigen-op reproduces the circulation signature "
                "lambda_k=1-exp(2 pi i k/n) on |lambda-1|=1 (matches closed form "
                "+ diagnostic oracle as a set)",
                {"oracle": oracle_report, "srmech": per_n})
    else:
        _record("4_gated_op_matches_oracle", "FAIL",
                "srmech directed eigen-op present but its spectrum does NOT "
                "match the circulation signature -- implementation regression",
                {"oracle": oracle_report, "srmech": per_n})


# --------------------------------------------------------------------------
# Driver.
# --------------------------------------------------------------------------
def main() -> int:
    print("=" * 74)
    print("DIRECTED / SIGNED LAPLACIAN EIGEN-OP SCAFFOLD  (honest_status=SCAFFOLD)")
    print("=" * 74)
    check1_no_directed_eigen_op()
    check2_target_on_circle()
    check3_symmetric_projection_differs()
    check4_gated_op_matches_oracle()

    c = results["counts"]
    print("-" * 74)
    print(f"COUNTS  PASS={c['PASS']}  SKIP={c['SKIP']}  "
          f"FAIL={c['FAIL']}  NULL={c['NULL']}")
    print("Expected on rc15: the GATED leg (CHECK 4) SKIPs; "
          "CHECKs 1-3 PASS (gap confirmed + target anchored).")
    print("-" * 74)
    print(json.dumps(results, indent=2, default=str))

    # Exit code: FAIL or NULL is a hard problem; SKIP on the gated leg is fine.
    return 1 if (c["FAIL"] > 0 or c["NULL"] > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
