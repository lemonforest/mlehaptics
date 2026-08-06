"""The generalised self-hosting import ban (`#T1073`, user-decided 2026-08-05).

ONE data-driven guard for every "srmech does not borrow this" rule. Adding a
new ban is a row in :data:`BAN_LIST` — a **data edit**, not a new test file.

It ABSORBS the three separate import ratchets that preceded it
(``test_no_stdlib_math_import`` rc13, ``test_numpy_carrier_ratchet`` rc69,
``test_no_stdlib_fractions_import`` rc263) and closes the gap ADR-0005 §2.4
named but the three files did not cover: **`decimal`**, plus the two
self-hosted wire codecs (**`json`** / **`tomllib`**-`tomli`).

Why one table instead of three files
====================================
ADR-0005 already states the rule in its general form — *"srmech source imports
NO external mathematics library — ever"* — and records WHY the general form
matters: the rule was first held as "numpy-free", then "no stdlib ``math``",
and stating only the instances is exactly what let ``fractions.Fraction``
in (it is neither) until it was load-bearing across ~20 modules. A separate
file per instance re-creates that failure shape one level up: the FOURTH ban
costs a new file, so it does not get written. A table costs a row.

The two stances this encodes
============================
**1. Projection is allowed; engine use is not.** *"we can let srmech project
to decimal when needed."* The ban is on using a foreign library as the
**computation engine**. srmech CONVERTING or EMITTING to a foreign type at an
output / interop boundary is legitimate. Hence :data:`MODE_ALLOWED_PROJECTION`
— a mode, not a flat blocklist.

**2. The ban is a COVERAGE instrument, not purity theatre.** *"this approach of
srmech tooling first also means we thoroughly test all our surfaces."*
Reaching for srmech first is how every shipped surface gets exercised and how
gaps become visible. So when this guard fires, the FIRST question is not "how
do I get an exemption" but **"does srmech already ship this and I did not
look?"** — twice in one session the answer was yes (``mat_rank``,
``srmech_double_repr``). That sentence is in the failure message on purpose.

The three modes
===============
``BANNED_ENGINE``
    srmech's own carrier IS the engine; the foreign module has no legitimate
    import at all. ``numpy`` / ``math`` / ``fractions``.

``ALLOWED_PROJECTION``
    Engine use banned; an import is legitimate ONLY from a file named in
    ``allowances`` as an output / interop projection boundary. ``decimal``.
    Its allowance set is EMPTY today — see "the decimal finding" below.

``FRONT_DOOR_ONLY``
    Not an engine at all — a wire codec srmech has already self-hosted behind
    its own front door (``srmech._json`` / ``srmech._toml``, native
    ``srmech_json`` / ``srmech_toml`` first, stdlib floor). A direct stdlib
    import BYPASSES the front door and is ledgered debt. ``json`` /
    ``tomllib`` / ``tomli``.

AST, never grep
===============
Every scan is an :mod:`ast` walk. This is a hard requirement, not a taste:

* It must resolve ``import decimal``, ``import decimal as X``,
  ``import decimal.sub``, and ``from decimal import Y`` — a naive
  ``startswith("import decimal")`` misses two of the four. Measured on this
  tree: an AST scan that only looked at ``ast.Import.names[0].name`` missed
  ``import json as _json`` in **9** modules.
* It must NOT count strings, comments or docstrings. Measured on this tree:
  grep counts **105** JSON write sites where the AST counts **64** — a 64%
  over-count, all prose. rc112 had already fixed this exact defect once, by
  hardening the numpy ratchet's ``startswith`` into a real-import regex after
  a docstring line wrapping to ``"import numpy lazily (the…"`` at column 0
  tripped it. The AST simply cannot make that mistake.
* It must see imports at ANY scope. ``ast.walk`` reaches function-local and
  ``try:``-block imports; the retired numpy ratchet's ``^import numpy`` line
  regex was column-0 only and would have missed a lazy in-function import.
  :func:`test_numpy_ast_engine_subsumes_the_retired_column0_regex` proves the
  migration only ever TIGHTENS.

``node.level`` is the discriminator that makes this safe: ADR-0010 created the
INTERNAL ``srmech.math`` namespace, and the AST records both ``from math import
sin`` and ``from .math import rational`` with ``node.module == "math"``. Only
``level == 0`` is the stdlib.

Proof it can go RED
===================
A strict-zero assertion over an already-empty population passes forever while
testing nothing. That is not hypothetical here — it is how rc403's float
defect hid behind a green corpus. So the non-vacuity proof SHIPS:
:func:`test_the_guard_fires_on_every_banned_import_form` runs the engine over
synthetic sources carrying each of the six import forms, for EVERY row in the
table, and fails if any form does not trip it;
:func:`test_the_guard_is_not_fooled_by_prose` runs it over the same module
names spelled only in a docstring, a comment and a string literal;
:func:`test_the_scanned_population_is_nonempty` fails if a scan root resolves
to zero files, which is the way a strict zero goes vacuous at the ROOT rather
than at the row.

The `_native/` scan hole this closes
====================================
The retired ``math`` / ``fractions`` guards both skipped any path with
``_native`` in its parts unless the file was named ``_native.py``, on the
comment *"_native/ holds only compiled libs in a wheel; nothing to scan
there."* That was true when written and is not true now:
``srmech/_native/__init__.py`` is a **1.1 MB generated Python module**, and it
was therefore exempt from both bans. This guard scans every ``.py`` under the
package with no exclusion. Verified at adoption: ``math`` and ``fractions``
stay at 0 with the hole closed, so closing it is free — but it was a real
hole, and a 1.1 MB module is not where you want one.

The decimal finding (reported, not built)
=========================================
``decimal`` ships at STRICT ZERO in the package with an EMPTY allowance set,
which is to say: **the projection mode is permitted-but-unused.** No
``decimal`` projection or adapter exists in srmech today. The one textual hit
under ``srmech/`` is ``math/rational.py``'s private ``_decimal_zfill``, a
zero-fill string helper — not a :class:`decimal.Decimal` anything.

What DOES exist is srmech's own decimal projection, and it is not the stdlib
module: **``srmech_double_repr``** (``c/include/srmech.h``), the rc403
integer-only Ryu shortest-round-trip ``double`` → decimal-string writer that
backs ``srmech_json``'s float output and the MCP marshaller. So the capability
"project a binary double to exact decimal text" is already self-hosted; the
stdlib ``decimal`` module is simply not needed for it. Nothing was built here
speculatively — this project has twice queued a phantom gap against code that
had already shipped, and this row records the measurement instead.

The json / tomli adjudication
=============================
Both are IN, and neither is a strict zero, because a strict zero would be a
lie about a mandatory floor:

* **``tomllib`` / ``tomli`` — strict zero outside 3 NAMED files each.** srmech
  self-hosts TOML behind ``srmech._toml.loads``. The three surviving stdlib
  imports are all named necessities, not bypasses: ``_toml.py`` carries the
  MANDATORY pure/Pyodide floor (no C library there), and ``amsc/descriptor.py``
  + ``profile_loader.py`` retain the alias solely for their
  ``except tomllib.TOMLDecodeError`` clauses — both parse through ``_toml``.
  (Checked, not assumed: the first read of these looked like front-door
  bypasses and they are not.)

* **``json`` — a down-only CEIL of 36 import statements**, plus the named
  ``_json.py`` front-door floor. The ceiling is pinned by the **WRITE** half.

  ⚠️ **The rc405 version of this bullet was wrong, and the correction is the
  point of rc406.** It read *"29 read-half uses, of which 28 are drainable"*.
  Three separate quantities had been collapsed into one number:

  ===========================  =====  =================================
  quantity                     count  what it actually is
  ===========================  =====  =================================
  ``import`` STATEMENTS          37   what this CEIL counts (32 files)
  READ call sites                18   ``json.loads`` x17 + ``json.load``
  WRITE call sites               64   ``dumps`` / ``dump``
  ===========================  =====  =================================

  The "29" was ``18 read calls + 11 ``json.JSONDecodeError`` TYPE REFERENCES`` —
  and an ``except json.JSONDecodeError`` clause is not a parse call and cannot
  be drained by definition. The "28 drainable" then asserted a drain that had
  **already happened**: rc401 repointed **27** sites onto ``_json.loads`` and
  left **17** deliberately fenced on a per-site allowlist, with the reason
  written at each site (11 PROTOCOL BOUNDARY — MCP JSON-RPC wire, bus wire,
  CLI/argv input, fetched HTTP bodies; 4 LAYERING inside ``_native``, where
  repointing would invert the dependency, since ``srmech._json`` is a CONSUMER
  of that shim; plus ``_json.py``'s own floor). So the drainable read half was
  **0**, not 28. ``test_json_read_selfhost_rc401.py`` pins the 27/17 split in
  both directions and would have contradicted the number on sight.

  What rc406 actually removed was **2 DEAD imports** — ``carrier_schema.py`` and
  ``responsion_schema.py``, repointed at rc401 with their ``import json`` left
  behind, so two fully-drained files were counted as borrowed forever. Nothing
  could see that (every guard here counts imports; the rc401 gate counts read
  CALLS), which is why :func:`test_no_banned_import_is_dead` now ships.

  39 -> 37 (2 dead imports) -> 36 (``_json.py`` reclassified from anonymous debt
  to a named front-door necessity, matching the ``tomllib`` row).

Where the numpy drainage ledger lives
=====================================
The retired ``test_numpy_carrier_ratchet.py`` carried ~400 lines of per-rc
commentary for the 61 → 0 drain (rc69 → rc127). That record is NOT lost and
is not duplicated here: it is committed per-flip in ``c/ROSETTA_LEDGER.md``
(~40 entries, each naming its ``CEIL_NUMPY_CARRIER`` transition) and per-rc in
``python/CHANGELOG.md`` (the rc127 capstone entry states the 1 → 0). The
constant name ``CEIL_NUMPY_CARRIER`` is deliberately KEPT below so those
records, and ``math/laplacian.py``'s docstring reference to it, stay live.

Pure stdlib (``ast`` / ``pathlib`` / ``re``); numpy-free; no ``abs()``.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import pytest

import srmech

# ── roots ─────────────────────────────────────────────────────────────
#
# The installed/edited package source root (…/srmech/), plus the two SUPPORTING
# roots beside it. `tools/` is the sharper of the two supporting roots: a
# GENERATOR that emitted a banned import would put it into `srmech/` itself,
# where the package scan only catches it after the next regen.
_PKG_ROOT = Path(srmech.__file__).resolve().parent
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TESTS_ROOT = _REPO_ROOT / "tests"
_TOOLS_ROOT = _REPO_ROOT / "tools"

SCOPE_PACKAGE = "package"
SCOPE_PACKAGE_AND_SUPPORTING = "package+tests+tools"

MODE_BANNED_ENGINE = "BANNED_ENGINE"

#: The foreign type may be produced at a boundary, never used as the engine.
#:
#: An import is legitimate ONLY from a file named in ``allowances``. Through
#: rc406 this said such a file must be "an output / interop projection
#: boundary", which was too narrow for its own ban list: rc407 (`#T1076`)
#: brought the `decimal` row's scope in line with its exact-arithmetic peer
#: `fractions` and the file it then had to name is
#: ``tests/test_classn_precision_wave2_rc320.py`` — an independent PRECISION
#: ORACLE, not a projection boundary at all.
#:
#: So an allowance under this mode may be either:
#:   * a **projection boundary** — srmech CONVERTING or EMITTING the foreign
#:     type at an output / interop edge (the original reading); or
#:   * an **independent oracle** (``_ORACLE``) — a TEST importing the foreign
#:     library to grade a srmech result against a reference srmech did not
#:     produce. This is the opposite of engine use: the whole point is that the
#:     foreign library does NOT share the carrier under test.
#:
#: What stays banned in both readings is identical, and it is the only thing
#: the mode was ever about: srmech IMPORTING the library to do its own math.
MODE_ALLOWED_PROJECTION = "ALLOWED_PROJECTION"
MODE_FRONT_DOOR_ONLY = "FRONT_DOOR_ONLY"

ENFORCE_STRICT_ZERO = "STRICT_ZERO"
ENFORCE_CEIL = "CEIL"

_MODES = {MODE_BANNED_ENGINE, MODE_ALLOWED_PROJECTION, MODE_FRONT_DOOR_ONLY}
_ENFORCEMENTS = {ENFORCE_STRICT_ZERO, ENFORCE_CEIL}
_SCOPES = {SCOPE_PACKAGE, SCOPE_PACKAGE_AND_SUPPORTING}

#: The numpy carrier ceiling, KEPT under its historical name (#564). rc127 drove
#: it to 0 and it is the permanent "no numpy carrier anywhere in srmech/" guard.
#: `srmech/math/laplacian.py` and `c/ROSETTA_LEDGER.md` both cite this name.
CEIL_NUMPY_CARRIER = 0

#: `json` import statements under `srmech/`, EXCLUDING the named front-door
#: floor in `_json.py`. DOWN-ONLY. This counts IMPORT STATEMENTS — not calls —
#: and what pins it is the **WRITE** half: 64 by-design-stdlib `dumps`/`dump`
#: sites. The READ half is already fully adjudicated (see the module docstring).
#: rc406 measured 39 -> 36. rc407 (`#T1076`) drains 36 -> 29:
#:
#:   -5  `srmech/_native/__init__.py` held five function-local `import json as
#:       _json`. NOTE: these were NOT simply deletable. The module-level import
#:       at `:70` binds `json`, NOT `_json`, and there is no module-level `_json`
#:       anywhere in that file (AST-verified), so deleting the five alone raises
#:       `NameError` at all seven `_json.` call sites. The drain therefore
#:       deletes the imports AND repoints the seven uses onto the module-level
#:       `json` — the same module object, so behaviour is identical.
#:   -2  the two `_EXC_TYPE_ALIAS` files, which imported the banned module ONLY
#:       to name `json.JSONDecodeError` in an `except` clause. `srmech._json`
#:       now re-exports it (see `_JSON_ALLOWANCES` above).
CEIL_STDLIB_JSON = 29


# ── the allowance ROLES ───────────────────────────────────────────────
#
# An allowance is per FILE and carries a reason from a REVIEWED set. A new file
# fails here until somebody adds it and says which role the foreign module is
# playing. Never a glob, never a directory — a blanket nobody re-reads is how an
# allowance rots.

#: The file imports the foreign type but NOT srmech's replacement — an
#: INDEPENDENT ORACLE. Using srmech's own carrier here would make the reference
#: share the very carrier under test, which is the oracle failure this project
#: keeps re-learning (rc352 retired one such self-comparison outright). The
#: foreignness is the point, and removing it would leave srmech checked only
#: against itself.
_ORACLE = "independent oracle: must NOT share the srmech carrier under test"

#: The file imports BOTH — an INTERCHANGE fixture proving srmech ACCEPTS the
#: foreign type on input via the numbers.Rational / as_integer_ratio protocol.
#: That acceptance is explicitly in scope; these are the tests that hold it to it.
_INTERCHANGE = "interchange fixture: proves srmech ACCEPTS the foreign type"

#: `tools/gen_carrier_examples_probe.py` builds a namespace in which carrier
#: CONSTRUCTION EXPRESSIONS are evaluated, one of which is literally
#: `"Fraction": "Fraction(3, 4)"` — the accepted interchange input, exercised.
#: It emits that as a STRING into a human-reviewed skeleton, so nothing it
#: writes ever puts a banned import into the package.
_PROBE_NS = "probe namespace: evals the accepted-interchange construction example"

#: srmech's own front door for this codec. It carries the MANDATORY stdlib floor
#: for pure / Pyodide wheels, where no C library exists to self-host onto. This
#: allowance is never removed — removing it would break the pure wheel.
_FRONT_DOOR_FLOOR = "front-door floor: the mandatory pure/Pyodide stdlib fallback"

#: The module parses through srmech's front door and retains the stdlib alias
#: SOLELY to name the exception type in an `except tomllib.TOMLDecodeError`
#: clause. The front door re-raises that exact type, so the error contract is
#: unchanged; the alias is a type reference, not a parse path.
_EXC_TYPE_ALIAS = "exception-type alias only: parsing goes through the front door"

_ROLES = {_ORACLE, _INTERCHANGE, _PROBE_NS, _FRONT_DOOR_FLOOR, _EXC_TYPE_ALIAS}


# ── the fractions supporting-root allowances (migrated verbatim, rc352) ──
#
# Under `tests/` and `tools/` the stdlib Fraction plays the OPPOSITE role to a
# self-hosting violation: it is the deliberately-FOREIGN exact rational, and
# that is exactly why it is there.
#
# THE DISCRIMINATOR (rewritten rc407, `#T1076`). This block used to say each
# file is "classified by a CHECKED signal (does it also import `Q` / `to_q`?)".
# That proxy is perfectly self-consistent — 0/25 `_ORACLE` rows imported `Q`,
# 37/37 `_INTERCHANGE` rows did — but it does not measure what the role STRINGS
# assert, and 16 rows carried the wrong role in BOTH directions because of it.
# `dense_solve(..., exact=True)`, `cd_mult`, `cd_promote` and `cycle_holonomy`
# all CONSUME `Fraction` and RETURN `Q`, so importing `Q` proves nothing about
# which way the value flows. The question that actually decides is:
#
#   does the `Fraction` expression compute a value FROM SCRATCH that is then
#   compared against a srmech result            -> `_ORACLE`
#   or does it flow INTO / OUT OF a srmech op as the accepted exact-rational
#   interchange type                            -> `_INTERCHANGE`
#
# No test outcome depends on the role (`test_every_allowance_carries_a_reviewed
# _reason` only asserts membership in `_ROLES`). It matters because the role
# ships in the failure message and tells a future reader which rows are safe to
# drain — and draining a TRUE oracle deletes the only independent reference in
# that file, which is the one mistake here that silently weakens a gate.
#
# NOT batch-converted, deliberately. rc407 re-stamped 16 rows and HELD ONE BACK:
# see `test_dense_solve_parity.py` below.
_FRACTIONS_ALLOWANCES: Mapping[str, str] = {
    "tests/test_algebra_inertia_rc349.py": _ORACLE,
    "tests/test_apagodu_zeilberger_rc53.py": _INTERCHANGE,
    "tests/test_best_rational_bignum_898.py": _ORACLE,
    "tests/test_carrier_contract_rc120.py": _INTERCHANGE,
    "tests/test_carrier_ladder_rc116.py": _INTERCHANGE,
    "tests/test_carrier_numeric_protocol_conformance_qi.py": _INTERCHANGE,
    "tests/test_carrier_numeric_protocol_conformance_rc11.py": _INTERCHANGE,
    # NOT re-stamped, and must not be: `:70-71` compute the ordinary complex
    # product from scratch in `Fraction` arithmetic against `cd.cd_mult`, and
    # the module docstring says "fixes the Python behaviour with from-scratch
    # references (no srmech import for the structural facts)". Moving this row
    # would INTRODUCE an error, not fix one.
    "tests/test_cascade_cayley_dickson_parity.py": _ORACLE,
    "tests/test_cascade_reorient_parity.py": _INTERCHANGE,
    "tests/test_cascade_sedenion_parity.py": _ORACLE,
    "tests/test_cascade_sedenion_register.py": _INTERCHANGE,
    "tests/test_classn_precision_wave2_rc320.py": _ORACLE,
    "tests/test_crt_reconstruct_rc45.py": _ORACLE,
    # HELD BACK from the rc407 re-stamp, on review, against the brief that
    # listed it for `_INTERCHANGE`. Both readings are defensible — `dense_solve`
    # does consume `Fraction` and return `Q` — but the file's own docstring
    # calls it "the EXACT-Fraction reference" and "exact-Fraction oracle, never
    # against numpy", and `:64` is a hand-written `_THIRD = Fraction(1, 3)` with
    # hand-written expected `Fraction` matrices below it. That from-scratch
    # constant is the SAME signal that keeps `test_schur_complement_dsl_stage.py`
    # an `_ORACLE`. Re-stamping it would have said a true oracle is safe to
    # drain, so it stays `_ORACLE`: borderline-by-review, recorded, not silent.
    "tests/test_dense_solve_parity.py": _ORACLE,
    "tests/test_discrete_writhe_cwf_rc313.py": _INTERCHANGE,
    "tests/test_eigvals_exact_complex_rc24.py": _INTERCHANGE,
    "tests/test_eigvec_exact_rc23.py": _INTERCHANGE,
    "tests/test_exact_eigvals_routing_rc21.py": _INTERCHANGE,
    "tests/test_fractions_to_q_rc263.py": _INTERCHANGE,
    "tests/test_gosper_rc41.py": _INTERCHANGE,
    "tests/test_jacobi_sncndn_series.py": _ORACLE,
    "tests/test_karatsuba_and_qpow_rc168.py": _INTERCHANGE,
    "tests/test_klein4_gain_laplacian_rc229.py": _INTERCHANGE,
    "tests/test_lll_rc221.py": _ORACLE,
    "tests/test_map_ml_inv_dense_solve_rc64.py": _INTERCHANGE,
    "tests/test_octonion_dft_rc111.py": _ORACLE,
    "tests/test_op_lane_rc347.py": _INTERCHANGE,
    "tests/test_op_provenance_c_rc171.py": _INTERCHANGE,
    "tests/test_op_provenance_rc117.py": _ORACLE,
    "tests/test_poly_rc38.py": _ORACLE,
    "tests/test_poly_rc39.py": _ORACLE,
    "tests/test_primitive_integer_vector_rc378.py": _INTERCHANGE,
    "tests/test_q_cross_gcd_mul_rc211.py": _ORACLE,
    "tests/test_q_cross_gcd_mul_rc220.py": _ORACLE,
    "tests/test_q_gosper_rc55.py": _INTERCHANGE,
    "tests/test_q_native_dispatch_rc167.py": _INTERCHANGE,
    "tests/test_q_wz_certificate_rc57.py": _INTERCHANGE,
    "tests/test_q_zeilberger_rc56.py": _INTERCHANGE,
    "tests/test_qalg_carrier_rc22.py": _INTERCHANGE,
    "tests/test_qalg_cdmult_c_rc160.py": _INTERCHANGE,
    "tests/test_qalg_eigvals_c_rc162.py": _INTERCHANGE,
    "tests/test_qalg_qvec_c_rc159.py": _INTERCHANGE,
    "tests/test_qarg_polar_rc31.py": _INTERCHANGE,
    "tests/test_qi_consumers.py": _INTERCHANGE,
    "tests/test_qi_native_parity.py": _ORACLE,
    "tests/test_qm_quaternion_rc109.py": _ORACLE,
    "tests/test_qmat_c_rc40.py": _INTERCHANGE,
    "tests/test_qmat_carrier_rc34.py": _INTERCHANGE,
    "tests/test_qpoly_rc54.py": _ORACLE,
    "tests/test_qprime_carrier_rc32.py": _INTERCHANGE,
    "tests/test_qrow_prose_constructors_rc113.py": _ORACLE,
    # Borderline-by-review, left `_ORACLE` deliberately: a hand-written
    # `_THIRD = Fraction(1, 3)` expected constant AND a `Fraction(g)`
    # out-projection, so it is both at once. The from-scratch constant decides.
    "tests/test_schur_complement_dsl_stage.py": _ORACLE,
    "tests/test_schur_dtn_rc1.py": _INTERCHANGE,
    "tests/test_thetasum_is_zero_sound_rc210.py": _INTERCHANGE,
    "tests/test_thetasum_soundness_battery_rc234.py": _INTERCHANGE,
    "tests/test_thetasum_z6_collapse_rc235.py": _INTERCHANGE,
    "tests/test_tripoly_rc52.py": _ORACLE,
    "tests/test_winding_fold_rc215.py": _ORACLE,
    "tests/test_wz_certificate_rc43.py": _INTERCHANGE,
    "tests/test_zeilberger_crt_route_rc47.py": _INTERCHANGE,
    "tests/test_zeilberger_rc42.py": _INTERCHANGE,
    "tools/gen_carrier_examples_probe.py": _PROBE_NS,
}

#: The JSON front-door allowance. Exactly the peer of `_toml.py` below, and it
#: is named for the same reason: `_json.py` carries the MANDATORY pure/Pyodide
#: stdlib floor, so its import can never be drained and does not belong in a
#: DOWN-ONLY debt ledger that is supposed to be drivable to a true floor.
#: (Through rc405 it sat inside `CEIL_STDLIB_JSON`, which meant the ceiling had
#: a permanent +1 no rc could ever remove — the toml row next door had already
#: modelled this correctly.)
_JSON_ALLOWANCES: Mapping[str, str] = {
    "srmech/_json.py": _FRONT_DOOR_FLOOR,
}

#: The TOML front-door allowances. Identical file set for both spellings — the
#: stdlib module is `tomllib` on 3.11+ and the `tomli` backport on 3.10, and
#: every site is the same version-branched pair.
#:
#: rc407 (`#T1076`) drained the two `_EXC_TYPE_ALIAS` rows, 3 -> 1. Both files
#: re-ran the `tomllib` / `tomli` version branch at module top solely to NAME the
#: type in an `except tomllib.TOMLDecodeError` clause — they already parsed
#: through `srmech._toml`. The front door now owns its exception contract
#: (`srmech._toml.TOMLDecodeError`, bound from the same backend the parse rides),
#: so the imports had nothing left to do and leaving the rows would trip
#: `test_no_allowance_has_gone_stale`.
_TOML_ALLOWANCES: Mapping[str, str] = {
    "srmech/_toml.py": _FRONT_DOOR_FLOOR,
}

#: The `decimal` allowance (rc407, `#T1076`). ONE named test oracle.
#:
#: `tests/test_classn_precision_wave2_rc320.py` imports `decimal` to back gate
#: G2's precision oracle for all seven Q61 float-projection ops — it is LIVE
#: (loads at `:268` x2, `:269`, `:293`), and it is the ONLY `decimal` import
#: anywhere outside `srmech/`. It is an independent reference the srmech result
#: is graded against, which is exactly what `_ORACLE` means.
#:
#: NOTE the mode/role tension, resolved in the mode prose below: an independent
#: test oracle is NOT a "projection boundary", so `MODE_ALLOWED_PROJECTION`'s
#: narrative had to be widened to admit an `_ORACLE` allowance. No test
#: cross-checks mode against role, so that is prose — but leaving it unwritten
#: would make this row self-contradictory.
_DECIMAL_ALLOWANCES: Mapping[str, str] = {
    "tests/test_classn_precision_wave2_rc320.py": _ORACLE,
}


@dataclass(frozen=True)
class BanEntry:
    """One row of the self-hosting ban list.

    ``ceiling`` is compared with ``==``, not ``<=`` — TIGHT, the same reason the
    Rosetta and numpy-math ratchets are tight. A count BELOW the ceiling means a
    callsite was removed without draining the ledger; a count ABOVE means the
    borrowed library came back. Both are findings.
    """

    module: str
    scope: str
    mode: str
    enforcement: str
    ceiling: int
    #: The srmech surface that replaces it. One line, and it must NAME the
    #: surface — this string is what the failure message points the reader at.
    replaces_with: str
    rationale: str
    allowances: Mapping[str, str] = field(default_factory=dict)
    #: Also flag executable ``<module>.<attr>`` access where the base is the bare
    #: name. Belt-and-braces for a module bound by something other than a plain
    #: import; carried forward from the rc13 ``math`` ratchet, which is the one
    #: entry that has ever had it.
    check_attribute_access: bool = False


BAN_LIST = (
    BanEntry(
        module="numpy",
        scope=SCOPE_PACKAGE,
        mode=MODE_BANNED_ENGINE,
        enforcement=ENFORCE_STRICT_ZERO,
        ceiling=CEIL_NUMPY_CARRIER,
        replaces_with="srmech.math.mat.Mat / vec.Vec / hdc.HV + the native dense kernels",
        rationale=(
            "numpy is GONE, not optional (#564, rc127): `pip install srmech` pulls "
            "no numpy and the whole package imports + runs numpy-absent. A "
            "top-level import would make a submodule unloadable on a real install."
        ),
    ),
    BanEntry(
        module="math",
        scope=SCOPE_PACKAGE,
        mode=MODE_BANNED_ENGINE,
        enforcement=ENFORCE_STRICT_ZERO,
        ceiling=0,
        replaces_with=(
            "srmech.math.rational (Class-N series-truncate sin/cos/exp/log/sqrt, "
            "4*atan(1) for pi) + the native srmech_isqrt"
        ),
        rationale=(
            "rc13 purged the last residue (math.isqrt -> srmech_isqrt + integer "
            "Newton; math.fsum -> Neumaier compensated sum; math.pi -> the Class-N "
            "atan cascade). A bare-C host has no Python stdlib and must reach the "
            "same numbers."
        ),
        check_attribute_access=True,
    ),
    BanEntry(
        module="fractions",
        scope=SCOPE_PACKAGE_AND_SUPPORTING,
        mode=MODE_BANNED_ENGINE,
        enforcement=ENFORCE_STRICT_ZERO,
        ceiling=0,
        replaces_with="srmech.math.q.Q / to_q (native srmech_rational_* + srmech_bigint)",
        rationale=(
            "rc263 purged the last residue; Q subsumed the registered 'Fraction' "
            "interchange carrier. A stdlib Fraction is still ACCEPTED on INPUT "
            "everywhere via the numbers.Rational / as_integer_ratio protocol — "
            "what is banned is srmech IMPORTING it to do its own math."
        ),
        allowances=_FRACTIONS_ALLOWANCES,
    ),
    BanEntry(
        module="decimal",
        scope=SCOPE_PACKAGE_AND_SUPPORTING,
        mode=MODE_ALLOWED_PROJECTION,
        enforcement=ENFORCE_STRICT_ZERO,
        ceiling=0,
        replaces_with=(
            "the exact interior is Q / srmech_bigint; the decimal PROJECTION is "
            "srmech's own srmech_double_repr (integer-only Ryu, c/include/srmech.h)"
        ),
        rationale=(
            "Float is the last mile only (ADR-0005 §2.5): exact work stays in the "
            "integer ALU all the way and a decimal appears only at the terminal "
            "projection boundary. Projection is PERMITTED — an import from a named "
            "projection-boundary file is legitimate — and the ceiling stays STRICT "
            "ZERO: unused in the PACKAGE, with one named oracle in tests. "
            "rc407 (`#T1076`) widened this row from SCOPE_PACKAGE to "
            "SCOPE_PACKAGE_AND_SUPPORTING so it matches its exact-arithmetic peer "
            "`fractions`, which was the ONLY row scanning tests/ + tools/. A live "
            "decimal oracle sat in tests/ unscanned and un-allowanced the whole "
            "time; widening the scope brings it under the guard and names it. "
            "Counterfactual EXECUTED: widening WITHOUT the allowance is 1 "
            "unallowed hit against ceiling 0 = RED; with it, GREEN, and both "
            "test_no_allowance_has_gone_stale and "
            "test_every_allowance_carries_a_reviewed_reason pass."
        ),
        allowances=_DECIMAL_ALLOWANCES,
    ),
    BanEntry(
        module="json",
        scope=SCOPE_PACKAGE,
        mode=MODE_FRONT_DOOR_ONLY,
        enforcement=ENFORCE_CEIL,
        ceiling=CEIL_STDLIB_JSON,
        replaces_with="srmech._json.loads (native srmech_json_parse first, stdlib floor)",
        rationale=(
            "srmech self-hosts the JSON READ half behind its own front door "
            "(`#T1008`). The READ half is DONE: rc401 repointed 27 call sites onto "
            "_json.loads and fenced the remaining 17 on a per-site allowlist that "
            "test_json_read_selfhost_rc401.py enforces in BOTH directions. What "
            "this ceiling counts is the WRITE half — 64 by-design-stdlib dumps/dump "
            "sites, because srmech_json_write_ws declines the non-finite floats "
            "json.dumps emits, and does not implement indent= or the second "
            "separators= grammar. DOWN-ONLY."
        ),
        allowances=_JSON_ALLOWANCES,
    ),
    BanEntry(
        module="tomllib",
        scope=SCOPE_PACKAGE,
        mode=MODE_FRONT_DOOR_ONLY,
        enforcement=ENFORCE_STRICT_ZERO,
        ceiling=0,
        replaces_with="srmech._toml.loads (native srmech_toml_parse first, stdlib floor)",
        rationale=(
            "srmech self-hosts TOML behind its own front door (`#T907` / `#T1008`). "
            "Every surviving stdlib import is a NAMED necessity: the mandatory "
            "pure/Pyodide floor inside _toml.py, and two except-clause type aliases "
            "in modules that already parse through the front door."
        ),
        allowances=_TOML_ALLOWANCES,
    ),
    BanEntry(
        module="tomli",
        scope=SCOPE_PACKAGE,
        mode=MODE_FRONT_DOOR_ONLY,
        enforcement=ENFORCE_STRICT_ZERO,
        ceiling=0,
        replaces_with="srmech._toml.loads (native srmech_toml_parse first, stdlib floor)",
        rationale=(
            "The Python 3.10 backport spelling of the tomllib row above; same three "
            "named files, same version-branched pairs."
        ),
        allowances=_TOML_ALLOWANCES,
    ),
)


# ── the AST engine ────────────────────────────────────────────────────


def _iter_scope_files(scope: str):
    """Yield ``(path, repo-relative posix key)`` for every ``.py`` in ``scope``.

    No ``_native/`` exclusion. The retired guards skipped it on the belief that
    it holds only compiled libraries; ``srmech/_native/__init__.py`` is a 1.1 MB
    generated Python module and was therefore unscanned. See the module
    docstring.
    """
    roots = [_PKG_ROOT]
    if scope == SCOPE_PACKAGE_AND_SUPPORTING:
        roots += [_TESTS_ROOT, _TOOLS_ROOT]
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                key = path.relative_to(_REPO_ROOT).as_posix()
            except ValueError:
                # An installed package outside the repo tree: key off the
                # package root so the message still names the module.
                key = "srmech/" + path.relative_to(_PKG_ROOT).as_posix()
            yield path, key


#: Parsed-tree and source caches. Without them this guard re-parses the 1.1 MB
#: generated `srmech/_native/__init__.py` once per (row x test) — measured 210s
#: for the file. One parse per source file brings it to ~10s, which is what a
#: ripple gate has to be.
_SOURCE_CACHE: dict = {}
_TREE_CACHE: dict = {}


def _source(path: Path):
    key = str(path)
    if key not in _SOURCE_CACHE:
        try:
            _SOURCE_CACHE[key] = path.read_text(encoding="utf-8")
        except OSError:
            _SOURCE_CACHE[key] = None
    return _SOURCE_CACHE[key]


def _tree(path: Path):
    key = str(path)
    if key not in _TREE_CACHE:
        src = _source(path)
        if src is None:
            _TREE_CACHE[key] = None
        else:
            try:
                _TREE_CACHE[key] = ast.parse(src, filename=key)
            except (SyntaxError, ValueError):
                _TREE_CACHE[key] = None            # unparseable → not our concern
    return _TREE_CACHE[key]


def import_hits(source: str, module: str, *, filename: str = "<scan>",
                check_attribute_access: bool = False):
    """Every real import of ``module`` in ``source``, as ``(lineno, form)``.

    Resolves all four import forms at ANY scope (module / function / class /
    ``try:`` block), and NEVER sees a string, comment or docstring:

    * ``import M``                 / ``import M as X``
    * ``import M.sub``             / ``import M.sub as X``
    * ``from M import Y``          / ``from M.sub import Y``

    A RELATIVE ``from .M import Y`` (``node.level > 0``) is the INTERNAL srmech
    namespace, not the stdlib — ADR-0010 created ``srmech.math``, and the AST
    records both with ``node.module == "math"``. ``level`` is the only
    discriminator, so it is checked on every ``ImportFrom``.
    """
    try:
        tree = ast.parse(source, filename=filename)
    except (SyntaxError, ValueError):
        return []                                  # unparseable → not our concern
    return _hits_from_tree(tree, module, check_attribute_access)


def _hits_from_tree(tree, module: str, check_attribute_access: bool):
    """The walk itself, over an already-parsed tree. See :func:`import_hits`."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module or alias.name.startswith(module + "."):
                    asname = f" as {alias.asname}" if alias.asname else ""
                    out.append((node.lineno, f"import {alias.name}{asname}"))
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:
                continue                           # relative → internal namespace
            mod = node.module or ""
            if mod == module or mod.startswith(module + "."):
                names = ", ".join(a.name for a in node.names)
                out.append((node.lineno, f"from {mod} import {names}"))
        elif check_attribute_access and isinstance(node, ast.Attribute):
            base = node.value
            if isinstance(base, ast.Name) and base.id == module:
                out.append((node.lineno, f"{module}.{node.attr}"))
    return sorted(out)


def _scan(entry: BanEntry):
    """``{repo-relative key: [violation strings]}`` for one ban entry."""
    found = {}
    for path, key in _iter_scope_files(entry.scope):
        tree = _tree(path)
        if tree is None:
            continue
        hits = _hits_from_tree(tree, entry.module, entry.check_attribute_access)
        if hits:
            found[key] = [f"{key}:{ln}: {form}" for ln, form in sorted(hits)]
    return found


def _unallowed(entry: BanEntry):
    return {k: v for k, v in _scan(entry).items() if k not in entry.allowances}


def _count(mapping):
    total = 0
    for hits in mapping.values():
        total += len(hits)
    return total


_TEACH = (
    "\n\nFIRST QUESTION — does srmech already ship this and you did not look? "
    "Twice in one session the answer was yes (`mat_rank`, `srmech_double_repr`). "
    "Check `srmech.describe()` / the introspect surface, and grep the C header, "
    "BEFORE concluding there is a gap. This ban is a COVERAGE instrument: "
    "reaching for srmech first is how every shipped surface gets exercised and "
    "how the real gaps become visible. If the surface genuinely does not exist, "
    "ADD it to srmech as a cascade (native C + Python) — never import it "
    "(ADR-0005 §2.1)."
)


def _ids(entries):
    return [e.module for e in entries]


# ── table hygiene ─────────────────────────────────────────────────────


def test_the_ban_table_is_well_formed():
    """Every row must be classified, not merely present."""
    seen = set()
    for e in BAN_LIST:
        assert e.module not in seen, f"duplicate ban row for {e.module!r}"
        seen.add(e.module)
        assert e.scope in _SCOPES, f"{e.module}: unknown scope {e.scope!r}"
        assert e.mode in _MODES, f"{e.module}: unknown mode {e.mode!r}"
        assert e.enforcement in _ENFORCEMENTS, (
            f"{e.module}: unknown enforcement {e.enforcement!r}")
        assert e.ceiling >= 0, f"{e.module}: negative ceiling"
        if e.enforcement == ENFORCE_STRICT_ZERO:
            assert e.ceiling == 0, (
                f"{e.module}: STRICT_ZERO with a nonzero ceiling is a "
                f"contradiction — use CEIL and say what the debt is")
        else:
            assert e.ceiling > 0, (
                f"{e.module}: a CEIL of 0 IS a strict zero — say so, so the "
                f"failure message tells the reader it may never be raised")
        # The replacement string is the whole point of the failure message: it
        # must NAME a srmech surface, not gesture at one.
        assert "srmech" in e.replaces_with, (
            f"{e.module}: replaces_with must NAME the srmech surface that "
            f"replaces the import; got {e.replaces_with!r}")
        assert len(e.rationale) > 60, f"{e.module}: rationale is a rubber stamp"


def test_the_scanned_population_is_nonempty():
    """A strict zero over an EMPTY population passes forever while testing
    nothing — that is how rc403's float defect hid behind a green corpus. This
    catches the vacuity at the ROOT (a mis-resolved scan path), which no
    per-row assertion can see."""
    assert _PKG_ROOT.is_dir(), f"package root did not resolve: {_PKG_ROOT}"
    pkg = list(_iter_scope_files(SCOPE_PACKAGE))
    both = list(_iter_scope_files(SCOPE_PACKAGE_AND_SUPPORTING))
    assert len(pkg) > 200, f"package scan found only {len(pkg)} .py files"
    assert len(both) > len(pkg) + 500, (
        f"supporting scan found only {len(both) - len(pkg)} extra files — "
        f"tests/ + tools/ did not resolve")
    # And the scan must actually reach INSIDE _native/, the hole this closes.
    keys = {k for _, k in pkg}
    assert "srmech/_native/__init__.py" in keys, (
        "the generated 1.1 MB srmech/_native/__init__.py is not being scanned — "
        "the `_native` exclusion hole has reopened")


# ── enforcement ───────────────────────────────────────────────────────


@pytest.mark.parametrize("entry", BAN_LIST, ids=_ids(BAN_LIST))
def test_module_is_at_its_enforcement_level(entry: BanEntry):
    unallowed = _unallowed(entry)
    count = _count(unallowed)
    if count == entry.ceiling:
        return
    listing = "\n  ".join(
        line for key in sorted(unallowed) for line in unallowed[key])
    if entry.enforcement == ENFORCE_STRICT_ZERO:
        head = (
            f"srmech imports the {entry.module!r} module ({entry.mode}). "
            f"This is a STRICT ZERO — it may never be raised.\n"
            f"Use instead: {entry.replaces_with}\n"
            f"Why: {entry.rationale}")
        if entry.allowances:
            head += (
                f"\nIf the FOREIGN module is genuinely the point here (an "
                f"independent oracle, an interchange fixture, or a named "
                f"front-door necessity), add the file to this entry's "
                f"`allowances` with the matching reason — one file, one reason, "
                f"never a glob.")
    else:
        direction = "ABOVE" if count > entry.ceiling else "BELOW"
        head = (
            f"{entry.module!r} import count {count} != ceiling {entry.ceiling} "
            f"({direction}). This ledger is DOWN-ONLY and TIGHT.\n"
            f"{direction} means: "
            + ("the borrowed module came back where a srmech surface belongs."
               if count > entry.ceiling else
               "a callsite was removed without draining the ledger — LOWER the "
               "ceiling to the new exact count.")
            + f"\nUse instead: {entry.replaces_with}\nWhy: {entry.rationale}")
    assert count == entry.ceiling, f"{head}{_TEACH}\n\nSites:\n  {listing}"


@pytest.mark.parametrize(
    "entry", [e for e in BAN_LIST if e.allowances],
    ids=_ids([e for e in BAN_LIST if e.allowances]))
def test_no_allowance_has_gone_stale(entry: BanEntry):
    """The allowance map is exact in BOTH directions.

    A listed file that no longer imports the module is as much a defect as an
    unlisted one that does: the allowance outlived its reason and is drifting
    toward a blanket permission nobody re-read. Same discipline as the JPL
    Rule-5 exempt list — an excuse must be counted, not granted.

    .. note::

       This test alone is NOT sufficient, and rc406 measured why: it asks
       whether the file still IMPORTS the module, which a DEAD import answers
       "yes" to forever. ``tests/test_infer_router_f929.py`` held an
       ``_INTERCHANGE`` allowance — *"proves srmech ACCEPTS the foreign type"* —
       on a ``from fractions import Fraction`` whose name the file never used,
       with a docstring claiming the use. The allowance covered nothing and this
       test could not see it. :func:`test_no_banned_import_is_dead` closes that.
    """
    importers = set(_scan(entry))
    stale = sorted(set(entry.allowances) - importers)
    assert not stale, (
        f"these files are named in the {entry.module!r} allowances but no longer "
        f"import it — the allowance is stale; DELETE the entry so it cannot "
        f"quietly cover a future import:\n  " + "\n  ".join(stale))


def _bound_names(tree, module: str):
    """``{bound name: [lineno, ...]}`` for every binding this module's imports make.

    ``import json`` and ``import json.decoder`` both bind ``json``; ``import json
    as _j`` binds ``_j``; ``from json import loads`` binds ``loads``.
    """
    bound: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module or alias.name.startswith(module + "."):
                    name = alias.asname or alias.name.split(".")[0]
                    bound.setdefault(name, []).append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:
                continue
            mod = node.module or ""
            if mod == module or mod.startswith(module + "."):
                for alias in node.names:
                    bound.setdefault(alias.asname or alias.name, []).append(node.lineno)
    return bound


@pytest.mark.parametrize("entry", BAN_LIST, ids=_ids(BAN_LIST))
def test_no_banned_import_is_dead(entry: BanEntry):
    """A borrowed import whose bound name is NEVER USED is a defect twice over.

    rc406 found two shapes of it in one scan, and neither had anything watching:

    1. **It holds an allowance open on nothing.**
       :func:`test_no_allowance_has_gone_stale` asks *"does this file still
       import the module?"* — and a dead import says yes forever. Measured:
       ``tests/test_infer_router_f929.py`` carried the ``_INTERCHANGE``
       allowance on a ``Fraction`` it never referenced.

    2. **It is permanent phantom debt in a DOWN-ONLY ledger.**
       ``CEIL_STDLIB_JSON`` counts import STATEMENTS. rc401 repointed
       ``introspect/carrier_schema.py`` and ``introspect/responsion_schema.py``
       onto ``srmech._json`` and left both ``import json`` lines behind, so two
       fully-drained files went on being counted as borrowed. The rc401 gate
       (``test_repointed_modules_bind_the_front_door``) checks only that no
       stdlib READ CALL survives — a bare import passes it cleanly.

    Both are invisible to every other guard here, which all count IMPORTS. This
    one counts USES, which is the question the allowance was really answering.

    A ``Name`` load covers both spellings: ``json.loads(...)`` puts ``json`` in a
    ``Load`` context as the attribute base, and ``loads(...)`` from a
    ``from``-import is a bare ``Name`` load. Annotations count as use.
    """
    dead = []
    for path, key in _iter_scope_files(entry.scope):
        tree = _tree(path)
        if tree is None:
            continue
        bound = _bound_names(tree, entry.module)
        if not bound:
            continue
        used = {n.id for n in ast.walk(tree)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        for name, linenos in sorted(bound.items()):
            if name not in used:
                dead.append(f"{key}:{linenos}: binds {name!r} and never uses it")
    assert not dead, (
        f"DEAD {entry.module!r} import(s) — the name is bound and never used.\n"
        f"DELETE the import. If the file is on this entry's `allowances`, delete "
        f"that row too: a dead import holds an allowance open over nothing, which "
        f"`test_no_allowance_has_gone_stale` cannot see (it checks for an IMPORT, "
        f"and a dead one is still an import). In a CEIL row it is worse — "
        f"permanent phantom debt in a DOWN-ONLY ledger.\n  " + "\n  ".join(dead))


def test_every_allowance_carries_a_reviewed_reason():
    """A reason that is empty, or not one of the reviewed roles, is a rubber
    stamp. The roles are the allowance's whole content."""
    bad = {}
    for e in BAN_LIST:
        for key, why in e.allowances.items():
            if why not in _ROLES:
                bad[f"{e.module}:{key}"] = why
    assert not bad, (
        f"an allowance carries an unreviewed reason; use one of the named roles "
        f"or add a new one DELIBERATELY: {bad}")
    for role in _ROLES:
        assert len(role) > 20, f"role string is too thin to be a reason: {role!r}"


def test_allowances_are_files_not_globs():
    """Never a glob, never a directory. A blanket cannot be re-read."""
    for e in BAN_LIST:
        for key in e.allowances:
            assert key.endswith(".py"), f"{e.module}: {key!r} is not a file"
            assert "*" not in key and "?" not in key, (
                f"{e.module}: {key!r} looks like a glob — allowances are per FILE")


# ── non-vacuity: the guard must be able to go RED ─────────────────────

#: Every import form the engine must resolve. `{m}` is the banned module.
_BANNED_FORMS = (
    "import {m}",
    "import {m} as _aliased",
    "import {m}.sub",
    "from {m} import thing",
    "from {m}.sub import thing",
    "def f():\n    import {m}\n    return {m}",      # function-scope, not column 0
)

#: The same module names spelled where the AST cannot see them.
_PROSE_FORMS = (
    '"""A docstring that says import {m} and from {m} import thing."""',
    "# a comment saying: import {m}",
    'TEXT = "import {m}"',
    'TEXT = """\nimport {m}\nfrom {m} import thing\n"""',
)


@pytest.mark.parametrize("entry", BAN_LIST, ids=_ids(BAN_LIST))
def test_the_guard_fires_on_every_banned_import_form(entry: BanEntry):
    """A guard that cannot fail is not a guard.

    Runs the engine over synthetic source carrying each import form. If ANY
    form comes back clean the guard is incomplete — that form is a hole a real
    import could walk through, which is precisely how ``import json as _json``
    stayed invisible to a naive AST scan in 9 modules.
    """
    for template in _BANNED_FORMS:
        source = template.format(m=entry.module)
        hits = import_hits(source, entry.module,
                           check_attribute_access=entry.check_attribute_access)
        assert hits, (
            f"the {entry.module!r} guard MISSES this import form — it is a hole:\n"
            f"{source}")


@pytest.mark.parametrize("entry", BAN_LIST, ids=_ids(BAN_LIST))
def test_the_guard_is_not_fooled_by_prose(entry: BanEntry):
    """The other half of non-vacuity: a guard that fires on prose is a guard
    people learn to ignore. rc112 hardened the numpy ratchet for exactly this
    after a docstring line wrapping to ``import numpy lazily (the…`` at column
    0 tripped it; grep over-counts JSON write sites 105 vs 64 the same way."""
    for template in _PROSE_FORMS:
        source = template.format(m=entry.module)
        hits = import_hits(source, entry.module,
                           check_attribute_access=entry.check_attribute_access)
        assert not hits, (
            f"the {entry.module!r} guard fires on PROSE — false positive:\n"
            f"{source}\ngot: {hits}")


@pytest.mark.parametrize("entry", BAN_LIST, ids=_ids(BAN_LIST))
def test_relative_imports_of_internal_namespaces_are_not_flagged(entry: BanEntry):
    """ADR-0010 created the INTERNAL ``srmech.math`` namespace, and the AST
    records ``from .math import rational`` with ``node.module == "math"`` —
    identical to the stdlib spelling but for ``node.level``. Without the level
    check this guard would false-flag every relative import of a srmech
    submodule; the same trap waits for any future ban whose name collides with
    an internal namespace."""
    for source in (f"from .{entry.module} import thing",
                   f"from ..{entry.module} import thing",
                   f"from .{entry.module}.sub import thing"):
        hits = import_hits(source, entry.module,
                           check_attribute_access=entry.check_attribute_access)
        assert not hits, (
            f"a RELATIVE import of an internal .{entry.module} namespace was "
            f"flagged as a stdlib import: {source!r} -> {hits}")


# ── cross-checks that the migration only tightened ────────────────────


@pytest.mark.parametrize("entry", BAN_LIST, ids=_ids(BAN_LIST))
def test_ast_hits_are_a_subset_of_what_a_text_grep_would_find(entry: BanEntry):
    """AST ⊆ grep, per entry.

    A real import statement always contains the module name on an ``import``
    line, so anything the AST finds a grep must also find. The converse is
    false and deliberately so (grep additionally matches prose — measured 105
    vs 64 on JSON write sites), which is why the ledger is AST-based. A file
    the AST flags that grep does NOT is an engine bug: it would mean the AST
    resolved an import whose source text does not contain one.
    """
    pattern = re.compile(
        r"(?:^|\W)(?:import\s+" + re.escape(entry.module) +
        r"\b|from\s+" + re.escape(entry.module) + r"[\s.])")
    for path, key in _iter_scope_files(entry.scope):
        tree = _tree(path)
        if tree is None:
            continue
        # attribute access has no import line for a grep to match
        ast_hits = _hits_from_tree(tree, entry.module, False)
        if not ast_hits:
            continue
        source = _source(path)
        assert pattern.search(source), (
            f"AST/grep DISAGREEMENT in {key}: the AST resolved "
            f"{[f for _, f in ast_hits]} but no text grep for "
            f"{entry.module!r} matches. That is an engine bug, not noise.")


def test_numpy_ast_engine_subsumes_the_retired_column0_regex():
    """The one engine CHANGE in the absorb, proved non-loosening.

    ``test_numpy_carrier_ratchet`` matched a column-0 ``import numpy`` line with
    a regex; this guard walks the AST. AST is strictly stronger on CODE (it also
    sees function-local and ``try:``-block imports) and strictly weaker on PROSE
    (it cannot see a docstring line) — and PROSE is the documented false-positive
    class rc112 hardened that very regex against. So the migration tightens where
    it matters. This pins the direction: every file the retired regex would flag
    must still be flagged here.
    """
    legacy = re.compile(
        r"^(?:import numpy(?:\.\w+)*(?:\s+as\s+\w+)?\s*(?:#.*)?$"
        r"|from numpy(?:\.\w+)*\s+import\s)")
    entry = next(e for e in BAN_LIST if e.module == "numpy")
    ast_files = set(_scan(entry))
    regex_files = set()
    for path, key in _iter_scope_files(SCOPE_PACKAGE):
        source = _source(path)
        if source is None:
            continue
        for line in source.splitlines():
            if legacy.match(line):
                regex_files.add(key)
                break
    missed = sorted(regex_files - ast_files)
    assert not missed, (
        "the AST engine MISSES a column-0 numpy import that the retired regex "
        "caught — the absorb LOOSENED a drained ratchet:\n  " + "\n  ".join(missed))
    assert len(ast_files) == CEIL_NUMPY_CARRIER
    assert len(regex_files) == CEIL_NUMPY_CARRIER


def test_mat_carrier_is_itself_numpy_free():
    """Carried forward by name from the retired numpy ratchet. Subsumed by the
    package-wide strict zero, and kept anyway: the 2-D carrier is the module
    that exists to DRIVE the ratchet down, so it earning a numpy import would be
    the single most confusing way for this to regress."""
    entry = next(e for e in BAN_LIST if e.module == "numpy")
    hits = _hits_from_tree(_tree(_PKG_ROOT / "math" / "mat.py"),
                           entry.module, False)
    assert not hits, (
        f"srmech.math.mat must stay numpy-free at import (lazy bridge only); "
        f"got {hits}")


def test_the_absorbed_guards_are_gone():
    """The absorb is complete, not additive.

    Three separate ratchet files are replaced by this table. If one comes back,
    there are two places to edit again and the FOURTH ban goes unwritten — which
    is the whole failure mode ADR-0005 §1 documents for the ban RULE and this
    guard exists to stop repeating for the ban ENFORCEMENT.
    """
    for name in ("test_no_stdlib_math_import.py",
                 "test_no_stdlib_fractions_import.py",
                 "test_numpy_carrier_ratchet.py"):
        assert not (_TESTS_ROOT / name).exists(), (
            f"{name} is back — its rule belongs in BAN_LIST as a row, so that "
            f"adding the next ban stays a data edit")


def test_no_banned_import_is_dead_anywhere():
    """**Strict-zero.** No banned-module import is DEAD, anywhere in the tree.

    The shipped ``test_no_banned_import_is_dead`` asks the same question but
    only inside each row's OWN scan scope, and six of the seven rows are
    ``SCOPE_PACKAGE``. At its own scope the answer is 0 for every row. Widen to
    package + tests + tools and rc406 measured **9** — 6 ``math`` and 3
    ``json``, every one under ``tests/``, every one outside its row's scan.
    Recounted with two independent liveness engines.

    WHY THIS IS NOT A RATCHET STEP, and must not be briefed as one: the drain
    moves **no ceiling, anywhere**. The counterfactual was executed — deleting
    all 9 in memory and re-running the shipped ``_count(_unallowed(...))`` gives
    every row delta **+0**, and no allowance goes stale. Swept tree-wide, no
    other ``CEIL_*`` ledger under ``tests/`` walks ``tests/`` or ``tools/``, and
    the numpy-math ratchet scans the package only. The value of the cleanup is
    entirely THIS guard; without it the 9 would simply come back.

    It reports DEADNESS, not presence, which is what lets it be strict-zero with
    no CEIL: the 88 LIVE ``math`` bindings across 87 test files are none of its
    business, so it cannot go red on legitimate foreign-oracle use — the very
    use the ``_ORACLE`` role exists to protect.

    Same syntactic-reference caveat as the tautology guard above: this is a
    reference count, not a liveness analysis.
    """
    dead = []
    for root in (_PKG_ROOT, _TESTS_ROOT, _TOOLS_ROOT):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue
            bound = _banned_bindings(tree)
            if not bound:
                continue
            loads = {
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
            }
            # A name re-exported through __all__ is referenced nowhere in its own
            # module by design — not dead. See _banned_bindings' docstring.
            for name in sorted(bound - loads - _reexported_names(tree)):
                dead.append(f"{path.relative_to(_REPO_ROOT)}: {name}")

    assert not dead, (
        f"{len(dead)} banned-module import(s) are DEAD — bound and never "
        f"referenced: {dead}. Delete them. A dead banned import is pure debt: "
        f"it moves no ceiling (these live outside every row's scan scope), it "
        f"proves nothing, and it makes the ledger describe a dependency the "
        f"file does not have.")


def _banned_bindings(tree: "ast.AST") -> set:
    """Names in this module bound by an import of a BAN_LIST module.

    TWO false-positive classes are excluded BY CONSTRUCTION, both found by these
    guards firing on a correct tree (rc407, `#T1076`) — a guard that fires is
    evidence, and both times the evidence was about the guard:

    1. **`node.level` is load-bearing.** srmech has its OWN ``srmech.math``
       subpackage, so ``from ..math.qmat import QMat`` has
       ``node.module == "math.qmat"`` and is indistinguishable from the stdlib
       ``math`` to a level-blind scan. A RELATIVE import can never be the stdlib
       module, so only ``level == 0`` counts. Without this, five srmech carriers
       (`Poly`, `QMat`, `Qalg`, `Qprime`, `TriPoly`), `srmech.math.q.Q` and
       `schur_complement` were all reported as dead *banned* imports.

    2. **`__all__` re-exports are not dead.** A name bound in an ``__init__.py``
       purely to re-export it is referenced nowhere in that file BY DESIGN. This
       is the exact false-positive `B8`'s alias-closure was rejected for — a
       legitimate ``Q = Fraction`` + ``__all__ = ["Q"]`` re-export must read
       LIVE. Handled by the caller via :func:`_reexported_names`.
    """
    banned = {entry.module for entry in BAN_LIST} | {"tomllib", "tomli"}
    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in banned:
                    bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # level > 0 is a RELATIVE import — srmech's own tree, never stdlib.
            if node.level == 0 and node.module and node.module.split(".")[0] in banned:
                for alias in node.names:
                    bound.add(alias.asname or alias.name)
    return bound


def _reexported_names(tree: "ast.AST") -> set:
    """Names listed in a module-level ``__all__`` — re-exported, so not dead."""
    out = set()
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
            continue
        value = node.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for element in value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    out.add(element.value)
    return out


def test_no_banned_import_is_kept_alive_by_a_tautology():
    """**Strict-zero.** No test function may exist ONLY to keep a banned import
    referenced.

    The shape: a test whose every ``Name`` Load is a banned-module binding — it
    touches NO srmech surface, so it cannot be exercising anything, and its only
    effect is to make ``test_no_banned_import_is_dead`` see the import as used.
    The rc163 instance said so in its own name (``test_unused_fraction_import``)
    and its own docstring ("Keep the Fraction import live"), and its ``_ORACLE``
    allowance therefore covered nothing: a semantic scan of that file returned
    ``srmech_touched = []``.

    MOTIVE, because it changes what this guard is for: the tautology was **not**
    written to defeat the detector. ``git show 6b6a93332`` puts it in the
    ORIGINAL rc163 commit (Jul 2026), ~240 rcs before ``test_no_banned_import_is
    _dead`` existed (rc406) and before the ``_ORACLE`` allowance itself (rc352).
    There is no linter in this repo — no ruff, flake8, setup.cfg, tox.ini or
    pre-commit. The import was **born dead** and was propped up by a test whose
    name concedes it. That STRENGTHENS the case for a mechanical guard: the
    shape arises innocently, so a code-review norm against bad-faith authorship
    cannot catch it.

    WHAT THIS CANNOT DECIDE — required honesty, and it is the same limit the
    sibling dead-import guard carries. ``{n.id for n in ast.walk(tree) if
    isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}`` is a **syntactic
    reference count, not a liveness analysis.** Ten defeat routes were probed
    and all ten read LIVE: ``_ = Fraction``, ``F = [Fraction][0]``,
    ``F, G = Fraction, 1``, ``T = {"q": Fraction}``, ``if False: Fraction(1,2)``,
    a never-called helper, and a bare ``x: Fraction`` annotation among them. A
    real fix needs use-before-read analysis plus an ``__all__``/re-export
    carve-out, and yields 0 files today — so it is deliberately NOT attempted
    here. This guard catches the shape that actually occurred.
    """
    offenders = []
    for root in (_TESTS_ROOT, _TOOLS_ROOT):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue
            bound = _banned_bindings(tree)
            if not bound:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith("test_"):
                    continue
                loads = {
                    sub.id
                    for sub in ast.walk(node)
                    if isinstance(sub, ast.Name)
                    and isinstance(sub.ctx, ast.Load)
                }
                if loads and loads <= bound:
                    offenders.append(f"{path.name}::{node.name}")

    assert not offenders, (
        f"{len(offenders)} test function(s) load NOTHING but a banned-module "
        f"binding: {offenders}. A test that touches no srmech surface is not "
        f"exercising anything — its only effect is to keep a dead import "
        f"looking live to test_no_banned_import_is_dead. Delete the test AND "
        f"the import, and drop the file's allowance row.")


def test_adr0005_table_matches_shipped_ledger():
    """ADR-0005 §2 clause 4 quotes this module's numbers — they must agree.

    THE DURABLE FIX. That table has drifted TWICE: at rc407 it still read
    "64 named tests/+tools/ oracle allowances" against a measured 63, and
    "down-only CEIL = 39" against a shipped 36. Both were prose nobody could
    fail. An ADR is the SSoT for a decision, so a stale number in it is worse
    than a stale number in a comment — it is what the next reader plans from.

    Skipped, not failed, when the ADR is absent: a wheel-only run has no
    `docs/srmech/adr/` and that is not a defect.
    """
    adr_dir = _REPO_ROOT.parent / "adr"
    matches = sorted(adr_dir.glob("0005-*.md")) if adr_dir.is_dir() else []
    if not matches:
        pytest.skip("ADR-0005 not present (wheel-only checkout)")

    text = matches[0].read_text(encoding="utf-8")

    frac = re.search(r"strict zero; (\d+) named `tests/`\+`tools/`", text)
    assert frac, (
        "could not find the fractions allowance count in ADR-0005 §2 clause 4 — "
        "if the table was reworded, update this parser with it")
    assert int(frac.group(1)) == len(_FRACTIONS_ALLOWANCES), (
        f"ADR-0005 says {frac.group(1)} fractions allowances; the shipped "
        f"ledger has {len(_FRACTIONS_ALLOWANCES)}. Update the ADR.")

    ceil = re.search(r"down-only CEIL = (\d+)", text)
    assert ceil, "could not find the json CEIL in ADR-0005 §2 clause 4"
    assert int(ceil.group(1)) == CEIL_STDLIB_JSON, (
        f"ADR-0005 says the json CEIL is {ceil.group(1)}; the shipped ceiling "
        f"is {CEIL_STDLIB_JSON}. Update the ADR.")


def test_every_oracle_row_documents_its_independence():
    """Every `_ORACLE` file says somewhere that it is an oracle / independent.

    **THIS IS A FLOOR, NOT A DISCRIMINATOR, AND MUST NOT BE PRESENTED AS ONE.**
    32 of 37 `_INTERCHANGE` rows carry the same wording — an 86% base rate — so
    a file passing this proves almost nothing about its role. It is also blind
    to the reverse direction, which is where 7 of the rc407 re-stamp's 16 errors
    lived: a mislabelled `_INTERCHANGE` row is invisible here by construction.

    What it DOES catch is the one asymmetric harm. The role tells a future
    reader which rows are safe to drain, and draining a true oracle deletes the
    only independent reference in that file. A row claiming `_ORACLE` while its
    file never once describes an independent reference is the shape most likely
    to be a mis-stamp in the dangerous direction.

    Do NOT batch-convert on this signal.
    """
    missing = []
    for relpath, role in sorted(_FRACTIONS_ALLOWANCES.items()):
        if role != _ORACLE:
            continue
        path = _REPO_ROOT / relpath
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        # The accepted vocabulary is the DISCRIMINATOR's own, documented at the
        # top of _FRACTIONS_ALLOWANCES: an oracle "computes a value FROM SCRATCH
        # that is then compared against a srmech result". rc407 first shipped
        # this accepting only "oracle"/"independent" and it fired on
        # test_cascade_cayley_dickson_parity.py — whose docstring says
        # "from-scratch references (no srmech import for the structural facts)",
        # i.e. the clearest possible statement of independence, in the exact
        # words this file teaches. A guard must accept the vocabulary it defines.
        if not any(w in text for w in
                   ("oracle", "independent", "from-scratch", "from scratch")):
            missing.append(relpath)

    assert not missing, (
        f"{len(missing)} `_ORACLE` row(s) never describe an independent "
        f"reference anywhere in the file: {missing}. Either the file really is "
        f"an oracle and should say so, or the role is wrong — and a wrong "
        f"`_ORACLE` tells the next reader a drainable row is load-bearing, "
        f"while a wrong `_INTERCHANGE` tells them a load-bearing row is "
        f"drainable. Read the Fraction sites and decide with the discriminator "
        f"at the top of _FRACTIONS_ALLOWANCES.")


def test_exact_arithmetic_rows_scan_supporting_scope():
    """Both exact-arithmetic rows scan tests/ + tools/, not just the package.

    A CONFIG PIN, and this docstring says so rather than dressing it as a
    behavioural proof. The behaviour was established by an EXECUTED
    counterfactual: widening `decimal` WITHOUT its allowance gives 1 unallowed
    hit against ceiling 0 = RED, at
    `tests/test_classn_precision_wave2_rc320.py:37`; with the allowance, GREEN.
    This test's job is narrower and worth having anyway — to stop the scope
    being silently re-narrowed later, which is exactly how the `decimal` oracle
    stayed invisible.

    Why THESE two rows: `fractions` and `decimal` are the exact-arithmetic pair,
    and a test that grades srmech's exact result against one of them is the
    `_ORACLE` pattern. Before rc407 `fractions` was the ONLY row in the whole
    table scanning the supporting tree, so a live `decimal` oracle sat outside
    every row's scan.

    NOT generalised to the other five rows on purpose: the asymmetry is
    `fractions`-vs-all-six, not `decimal`-vs-`fractions`. `math` at package
    scope is the next-nearest peer, and widening it is explicitly the WRONG
    move — it carries `check_attribute_access=True`, so a full-scope ceiling
    would be ~499 rather than the ~88 a unique-binding count suggests, and its
    stdlib `math` in tests IS the deliberately-foreign oracle the `_ORACLE` role
    exists to protect.
    """
    rows = {entry.module: entry for entry in BAN_LIST}
    for module in ("fractions", "decimal"):
        assert module in rows, f"no BAN_LIST row for {module!r}"
        assert rows[module].scope == SCOPE_PACKAGE_AND_SUPPORTING, (
            f"the {module!r} row scans {rows[module].scope!r}, not "
            f"{SCOPE_PACKAGE_AND_SUPPORTING!r}. Both exact-arithmetic rows must "
            f"scan tests/ + tools/: an oracle that grades srmech against the "
            f"foreign library lives in tests/, so a package-only scope cannot "
            f"see it and the allowance table silently stops describing reality."
        )

    # The oracle the widening exists to cover must actually be named.
    assert rows["decimal"].allowances, (
        "the decimal row scans tests/ but names no allowance — the live oracle "
        "at tests/test_classn_precision_wave2_rc320.py would be an unallowed "
        "hit against ceiling 0")
