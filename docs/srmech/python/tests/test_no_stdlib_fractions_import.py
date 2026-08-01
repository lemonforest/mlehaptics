"""No-stdlib-``fractions`` ratchet (v0.9.0rc263, #845).

srmech carries its exact rationals in its OWN C-native carrier
:class:`srmech.math.q.Q` — a reduced ``(num, den)`` integer pair whose reduce /
multiply ride the native ``srmech_rational_*`` / ``srmech_bigint`` symbols. It
therefore borrows **nothing** from the stdlib ``fractions`` module: rc263 purged
the last residue (the Cayley–Dickson element carrier, the exact-LA
``dense_solve`` / ``schur_complement`` boundary, ``cycle_holonomy``'s exact
holonomies, the Sturm / complex-isolation interval oracles, the arithmetic-coder,
the MCP charge wire, and every ``_coerce`` accept-branch), so a bare-C host with
no Python stdlib carries the same exact-rational math. The former registered
``"Fraction"`` interchange carrier was removed — ``Q`` subsumed it
(``[[feedback_prefer_carrier_native_arithmetic_over_downcast_decline]]`` /
``[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]``
generalised from ``math`` to ``fractions``).

A stdlib ``fractions.Fraction`` is still ACCEPTED on INPUT everywhere (``Q``'s
arithmetic + ``to_q`` speak the ``numbers.Rational`` / ``as_integer_ratio``
numeric protocol), and prose mentions of ``fractions.Fraction`` in docstrings /
comments are fine (the AST never sees them) — the framework can still *describe*
the interchange it accepts and the type it replaced. What is banned is srmech
*importing* ``fractions`` for its own math: this ratchet AST-walks every
``srmech/`` source module and fails on any ``import fractions`` /
``from fractions import`` statement (module or function scope). Pure stdlib
(``ast`` / ``pathlib``); numpy-free.
"""
from __future__ import annotations

import ast
from pathlib import Path

import srmech

# The installed/edited package source root (…/srmech/). Walk every .py under it.
_PKG_ROOT = Path(srmech.__file__).resolve().parent

# rc352: the two SUPPORTING roots. `tests/` and `tools/` sit beside the package
# and were previously unscanned, which is where a stdlib import would creep back
# in first — and `tools/` is the sharper of the two, because a GENERATOR that
# emitted `import fractions` would put the import into `srmech/` itself, where
# the package scan above would only catch it after the next regen.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TESTS_ROOT = _REPO_ROOT / "tests"
_TOOLS_ROOT = _REPO_ROOT / "tools"


# ── the NAMED allowances (rc352) ──────────────────────────────────────
#
# The ban is on **srmech doing its own math with a borrowed carrier**. Under
# `tests/` and `tools/` the stdlib Fraction plays the opposite role: it is the
# deliberately-FOREIGN exact rational, and that is exactly why it is there. Two
# roles, and each allowed file is classified into one by a CHECKED signal (does
# the file also import `Q` / `to_q`?), never by a filename pattern:

#: The file imports Fraction but NOT `Q` — an INDEPENDENT ORACLE. Using `Q`
#: here would make the reference share the very carrier under test, which is the
#: oracle failure this project keeps re-learning (rc352 retired one such
#: self-comparison outright). The foreignness is the point.
_ORACLE = "independent oracle: must NOT share the Q carrier under test"

#: The file imports BOTH — an INTERCHANGE fixture proving srmech ACCEPTS a
#: stdlib Fraction on input via the numbers.Rational / as_integer_ratio
#: protocol. The module docstring above says that acceptance is explicitly in
#: scope; these are the tests that hold it to it.
_INTERCHANGE = "interchange fixture: proves srmech ACCEPTS the foreign type"

#: `tools/gen_carrier_examples_probe.py` builds a namespace in which carrier
#: CONSTRUCTION EXPRESSIONS are evaluated, one of which is literally
#: `"Fraction": "Fraction(3, 4)"` — the accepted interchange input, exercised.
#: It emits that as a STRING into a human-reviewed skeleton, so nothing it
#: writes ever puts an `import fractions` into the package.
_PROBE_NS = "probe namespace: evals the accepted-interchange construction example"

#: Every file under `tests/` or `tools/` allowed to import the stdlib module,
#: named ONE BY ONE with its reason. A new file is a DECISION: it fails here
#: until somebody adds it and says which role it plays. The map is exact in BOTH
#: directions — a listed file that no longer imports `fractions` also fails, so
#: the allowance cannot rot into a permanent blanket.
_ALLOWED_SUPPORTING = {
    "tests/test_algebra_inertia_rc349.py": _ORACLE,
    "tests/test_apagodu_zeilberger_rc53.py": _INTERCHANGE,
    "tests/test_best_rational_bignum_898.py": _ORACLE,
    "tests/test_carrier_contract_rc120.py": _ORACLE,
    "tests/test_carrier_ladder_rc116.py": _INTERCHANGE,
    "tests/test_carrier_numeric_protocol_conformance_qi.py": _INTERCHANGE,
    "tests/test_carrier_numeric_protocol_conformance_rc11.py": _INTERCHANGE,
    "tests/test_cascade_cayley_dickson_parity.py": _ORACLE,
    "tests/test_cascade_reorient_parity.py": _ORACLE,
    "tests/test_cascade_sedenion_parity.py": _ORACLE,
    "tests/test_cascade_sedenion_register.py": _ORACLE,
    "tests/test_classn_precision_wave2_rc320.py": _ORACLE,
    "tests/test_crt_reconstruct_rc45.py": _ORACLE,
    "tests/test_dense_solve_parity.py": _ORACLE,
    "tests/test_discrete_writhe_cwf_rc313.py": _ORACLE,
    "tests/test_eigvals_exact_complex_rc24.py": _INTERCHANGE,
    "tests/test_eigvec_exact_rc23.py": _INTERCHANGE,
    "tests/test_exact_eigvals_routing_rc21.py": _ORACLE,
    "tests/test_fractions_to_q_rc263.py": _INTERCHANGE,
    "tests/test_gosper_rc41.py": _INTERCHANGE,
    "tests/test_infer_router_f929.py": _INTERCHANGE,
    "tests/test_jacobi_sncndn_series.py": _ORACLE,
    "tests/test_karatsuba_and_qpow_rc168.py": _INTERCHANGE,
    "tests/test_klein4_gain_laplacian_rc229.py": _ORACLE,
    "tests/test_lll_rc221.py": _ORACLE,
    "tests/test_map_ml_inv_dense_solve_rc64.py": _INTERCHANGE,
    "tests/test_octonion_dft_rc111.py": _ORACLE,
    "tests/test_op_lane_rc347.py": _ORACLE,
    "tests/test_op_provenance_c_rc171.py": _ORACLE,
    "tests/test_op_provenance_rc117.py": _ORACLE,
    "tests/test_poly_rc38.py": _INTERCHANGE,
    "tests/test_poly_rc39.py": _INTERCHANGE,
    "tests/test_q_cross_gcd_mul_rc211.py": _INTERCHANGE,
    "tests/test_q_cross_gcd_mul_rc220.py": _INTERCHANGE,
    "tests/test_q_gosper_rc55.py": _INTERCHANGE,
    "tests/test_q_native_dispatch_rc167.py": _INTERCHANGE,
    "tests/test_q_wz_certificate_rc57.py": _INTERCHANGE,
    "tests/test_q_zeilberger_rc56.py": _INTERCHANGE,
    "tests/test_qalg_carrier_rc22.py": _INTERCHANGE,
    "tests/test_qalg_cdmult_c_rc160.py": _ORACLE,
    "tests/test_qalg_eigvals_c_rc162.py": _INTERCHANGE,
    "tests/test_qalg_eigvec_c_rc163.py": _ORACLE,
    "tests/test_qalg_qvec_c_rc159.py": _INTERCHANGE,
    "tests/test_qarg_polar_rc31.py": _INTERCHANGE,
    "tests/test_qi_consumers.py": _INTERCHANGE,
    "tests/test_qi_native_parity.py": _INTERCHANGE,
    "tests/test_qm_quaternion_rc109.py": _ORACLE,
    "tests/test_qmat_c_rc40.py": _INTERCHANGE,
    "tests/test_qmat_carrier_rc34.py": _INTERCHANGE,
    "tests/test_qpoly_rc54.py": _INTERCHANGE,
    "tests/test_qprime_carrier_rc32.py": _INTERCHANGE,
    "tests/test_qrow_prose_constructors_rc113.py": _ORACLE,
    "tests/test_schur_complement_dsl_stage.py": _ORACLE,
    "tests/test_schur_dtn_rc1.py": _INTERCHANGE,
    "tests/test_thetasum_is_zero_sound_rc210.py": _INTERCHANGE,
    "tests/test_thetasum_soundness_battery_rc234.py": _INTERCHANGE,
    "tests/test_thetasum_z6_collapse_rc235.py": _INTERCHANGE,
    "tests/test_tripoly_rc52.py": _INTERCHANGE,
    "tests/test_winding_fold_rc215.py": _ORACLE,
    "tests/test_wz_certificate_rc43.py": _INTERCHANGE,
    "tests/test_zeilberger_crt_route_rc47.py": _INTERCHANGE,
    "tests/test_zeilberger_rc42.py": _INTERCHANGE,
    "tools/gen_carrier_examples_probe.py": _PROBE_NS,
}


def _iter_source_files():
    for path in sorted(_PKG_ROOT.rglob("*.py")):
        # _native/ holds only compiled libs in a wheel; nothing to scan there.
        if "_native" in path.parts and path.name != "_native.py":
            continue
        yield path


def _iter_supporting_files():
    """Every `.py` under `tests/` and `tools/`, with its repo-relative key."""
    for root in (_TESTS_ROOT, _TOOLS_ROOT):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path, path.relative_to(_REPO_ROOT).as_posix()


def _fractions_violations(path: Path, rel=None):
    """Return human-readable violations for one module (empty list = clean).

    ``rel`` is the label the violation is reported under. It defaults to the
    package-relative path (the original behaviour); the supporting-root scan
    passes a repo-relative one, because a file under ``tests/`` or ``tools/``
    has no ``_PKG_ROOT`` to be relative TO and ``Path.relative_to`` would raise.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []                                  # unreadable → not our concern
    out = []
    if rel is None:
        rel = path.relative_to(_PKG_ROOT)
    for node in ast.walk(tree):
        # `import fractions` / `import fractions as F`
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fractions" or alias.name.startswith("fractions."):
                    out.append(f"{rel}:{node.lineno}: import {alias.name}")
        # `from fractions import ...`
        elif isinstance(node, ast.ImportFrom):
            if node.module == "fractions" or (node.module or "").startswith("fractions."):
                names = ", ".join(a.name for a in node.names)
                out.append(f"{rel}:{node.lineno}: from {node.module} import {names}")
    return out


def test_no_stdlib_fractions_import_anywhere_in_source():
    violations = []
    for path in _iter_source_files():
        violations.extend(_fractions_violations(path))
    assert not violations, (
        "srmech imports the stdlib `fractions` module for its own math — it must "
        "not (#845). Carry the exact rational in srmech's own `Q` carrier "
        "(`from srmech.math.q import Q, to_q`); a stdlib Fraction is still "
        "accepted on INPUT via the numeric protocol, never imported:\n  "
        + "\n  ".join(violations)
    )


# ── rc352: the same strict zero over `tests/` and `tools/` ────────────


def _supporting_importers():
    """``{repo-relative path: [violation strings]}`` for every supporting file
    that imports the stdlib module — allowed or not."""
    found = {}
    for path, rel in _iter_supporting_files():
        hits = _fractions_violations(path, rel)
        if hits:
            found[rel] = hits
    return found


def test_no_unnamed_fractions_import_under_tests_and_tools():
    """STRICT ZERO outside the named allowances.

    The package scan above cannot see `tests/` or `tools/`, and `tools/` is the
    one that matters most: those scripts GENERATE package source, so a generator
    reaching for `fractions` would land the import inside `srmech/` and only be
    caught after the next regen. Here it is caught at the source.

    An allowance is per FILE and carries a reason — never a glob, never a
    directory. Adding a file is a deliberate act that names which role the
    foreign type is playing.
    """
    unnamed = {rel: hits for rel, hits in _supporting_importers().items()
               if rel not in _ALLOWED_SUPPORTING}
    assert not unnamed, (
        "a file under tests/ or tools/ imports the stdlib `fractions` module "
        "without a named allowance (#845 / #870, scope extended rc352).\n"
        "If srmech's own `Q` should be carrying this rational, use it "
        "(`from srmech.math.q import Q, to_q`).\n"
        "If the STDLIB type is the point — an independent oracle that must not "
        "share the carrier under test, or a fixture proving srmech ACCEPTS the "
        "foreign type on input — add the file to _ALLOWED_SUPPORTING with the "
        "matching reason:\n  "
        + "\n  ".join(f"{rel}: {'; '.join(hits)}"
                      for rel, hits in sorted(unnamed.items()))
    )


def test_the_fractions_allowance_has_not_gone_stale():
    """The map is exact in BOTH directions.

    A listed file that no longer imports `fractions` is just as much a defect as
    an unlisted one that does: it means the allowance outlived its reason and is
    drifting toward a blanket permission nobody re-read. Same discipline as the
    pure-by-design skip audit — an excuse must be counted, not granted.
    """
    importers = set(_supporting_importers())
    stale = sorted(set(_ALLOWED_SUPPORTING) - importers)
    assert not stale, (
        "these files are named in _ALLOWED_SUPPORTING but no longer import the "
        "stdlib `fractions` module — the allowance is stale; delete the entry so "
        "it cannot quietly cover a future import:\n  " + "\n  ".join(stale)
    )


def test_every_allowance_carries_a_real_reason():
    """A reason string that is empty, or not one of the three reviewed roles, is
    a rubber stamp. The roles are the allowance's whole content."""
    known = {_ORACLE, _INTERCHANGE, _PROBE_NS}
    bad = {rel: why for rel, why in _ALLOWED_SUPPORTING.items()
           if why not in known}
    assert not bad, (
        "an allowance carries an unreviewed reason; use one of the three named "
        f"roles or add a fourth deliberately: {bad}")
    assert all(len(r) > 20 for r in known)
