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
#: rc406 measured 39 -> 36.
CEIL_STDLIB_JSON = 36


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
# that is exactly why it is there. Each file is classified by a CHECKED signal
# (does it also import `Q` / `to_q`?), never by a filename pattern.
_FRACTIONS_ALLOWANCES: Mapping[str, str] = {
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
    "tests/test_primitive_integer_vector_rc378.py": _INTERCHANGE,
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
_TOML_ALLOWANCES: Mapping[str, str] = {
    "srmech/_toml.py": _FRONT_DOOR_FLOOR,
    "srmech/amsc/descriptor.py": _EXC_TYPE_ALIAS,
    "srmech/profile_loader.py": _EXC_TYPE_ALIAS,
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
        scope=SCOPE_PACKAGE,
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
            "projection-boundary file is legitimate — but the allowance set is "
            "EMPTY: no decimal projection exists in srmech today, because the "
            "capability is already self-hosted in C as srmech_double_repr."
        ),
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
