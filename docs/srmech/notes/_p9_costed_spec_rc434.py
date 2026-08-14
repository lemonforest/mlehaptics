"""`#T1130` P9 — the consolidated per-site ruling table, emitted as NDJSON.

Every row here is backed by an EXECUTION record in one of
``_p3_execute_declared_rc434.ndjson`` / ``_p4_refined_probes_rc434.ndjson`` /
``_p5_surfaces_and_overlap_rc434.ndjson`` / ``_p6_cross_surface_rc434.ndjson`` /
``_p7_uint64_family_sweep_rc434.ndjson``.  Nothing is ruled from reading a call
site.  Rulings are (a) FIX THE CODE / (b) FIX THE PROSE / (c) NOT-A-DEFECT.
"""

from __future__ import annotations

import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
OUT = os.path.join(REPO, "docs/srmech/notes/_p9_costed_spec_rc434.ndjson")
sys.path.insert(0, os.path.join(REPO, "docs/srmech/python"))

SITES = [
    dict(
        site_id="T1130-1",
        surface="docstring (Raises: block)",
        path="docs/srmech/python/srmech/cascade/composites.py:276",
        op="srmech.cascade.cyclic_gcd",
        declared="ValueError for 'negative inputs OR inputs exceeding the uint64 parity surface'",
        enforced_by_execution="ValueError for negative; NO RAISE for oversize (cyclic_gcd(2**64,5) -> 1)",
        direction="DECLARED-NOT-ENFORCED (clause-level: 1 of 2 clauses false)",
        ruling="b",
        ruling_justification=(
            "The CODE is correct BY AN EXPLICIT DESIGN DECISION, not merely current: "
            "rc167 (#765) removed gcd's compiled-in uint64 rejection under the "
            "no-compiled-in-caps discipline, and gcd's OWN docstring documents the "
            "removal ('No upper cap (arbitrary precision)'). Re-adding the cap would "
            "break the ~100-digit One-scale rationals that depend on it. The alias "
            "docstring simply failed to follow the primitive it forwards to."
        ),
        proposed_type="n/a (delete the false clause; keep the true negative-input clause)",
        evidence="_p3(composites.cyclic_gcd/oversize), _p4(3 magnitudes), _p7(CLAIM_FALSE_NO_RAISE)",
        cost="1 docstring edit, 2 sentences (Raises block + body prose); no regen",
    ),
    dict(
        site_id="T1130-2",
        surface="ToolEntry explanation (CURATED - authoring surface)",
        path="docs/srmech/python/srmech/introspect/_tool_docs_curated.py:1789",
        op="srmech.cascade.cyclic_gcd",
        declared="'negatives and values past uint64 raise ValueError'",
        enforced_by_execution="negatives raise; past-uint64 returns a value",
        direction="DECLARED-NOT-ENFORCED",
        ruling="b",
        ruling_justification="same design decision as T1130-1",
        proposed_type="n/a",
        evidence="_p6 verbatim, _p7 CLAIM_FALSE_NO_RAISE",
        cost=(
            "1 curated edit + regen ripple into _tool_docs.py:193 and "
            "c/src/srmech_tool_registry.c:11586 (downstream, not separate defects)"
        ),
    ),
    dict(
        site_id="T1130-3",
        surface="ToolEntry explanation (CURATED - authoring surface)",
        path="docs/srmech/python/srmech/introspect/_tool_docs_curated.py:1965",
        op="srmech.math.cyclic.gcd",
        declared=(
            "'two NON-NEGATIVE integers, both bounded by uint64' + "
            "'A negative argument or one past 2**64 raises ValueError'"
        ),
        enforced_by_execution="negatives raise; past-2**64 returns a value (uncapped)",
        direction="DECLARED-NOT-ENFORCED, and CONTRADICTS this op's own docstring",
        ruling="b",
        ruling_justification=(
            "Strongest (b) in the set: the op's own docstring already states the "
            "correct contract, so the registry text is the sole stale surface and "
            "there is no gap being documented away."
        ),
        proposed_type="n/a",
        evidence="_p6 verbatim, _p7 CLAIM_FALSE_NO_RAISE",
        cost=(
            "1 curated edit + regen ripple into _tool_docs.py:317 and "
            "c/src/srmech_tool_registry.c:5026"
        ),
    ),
    dict(
        site_id="T1130-4",
        surface="docstring (Raises: block)",
        path="docs/srmech/python/srmech/music/_spectra.py:409",
        op="srmech.music.common_period",
        declared="ValueError, TypeError only",
        enforced_by_execution=(
            "OverflowError('lcm(614889782588491410, 53) overflows uint64') on a "
            "harmonic spectrum whose reduced-denominator lcm passes the Class-I "
            "parity surface"
        ),
        direction="ENFORCED-NOT-DECLARED",
        ruling="b",
        ruling_justification=(
            "The raise is CORRECT and deliberate: _CLASS_I_PARITY_MAX is documented "
            "in-module as 'a real C-parity contract and is NOT relaxed here', and the "
            "sibling _period_multiplier_or_unavailable exists precisely to report the "
            "same condition without raising. The docstring is incomplete, not the code."
        ),
        proposed_type="OverflowError (adopts the shipped cyclic.lcm precedent)",
        evidence="_p5(common_period/OVERFLOW-undeclared -> ENFORCED)",
        cost="1 docstring line; regen ripple if the op's ToolEntry is reseeded",
    ),
    dict(
        site_id="T1130-5",
        surface="docstring (absent Raises: block) x 10 registered tools",
        path="see _p6_cross_surface_rc434.ndjson REGISTRY_RIGHT_DOCSTRING_SILENT rows",
        op=(
            "cyclic.gcd, exact_dft.exact_idft, genome.centromere, cascade.cyclic_mod_mul, "
            "cascade.cyclic_mod_mul_wide, cascade.hamming_syndrome, qpoly_from_coeffs, "
            "qbipoly_from_coeffs, tool_schema_view, music.normal_order"
        ),
        declared="nothing in the docstring; the ToolEntry prose names the exception",
        enforced_by_execution="the named exception IS raised (10/10)",
        direction="ENFORCED-NOT-DECLARED (docstring silent, registry correct)",
        ruling="b",
        ruling_justification=(
            "Execution confirms the registry, so the code is right and the docstring "
            "is the incomplete surface. No gap is being documented away — the "
            "declaration is being ADDED, not removed."
        ),
        proposed_type="as observed per op (8 ValueError, 4 TypeError across the rows)",
        evidence="_p6 tally REGISTRY_RIGHT_DOCSTRING_SILENT=10",
        cost="10 docstring Raises: blocks; no code change",
    ),
    dict(
        site_id="T1130-C1",
        surface="docstring (Raises: block) x 49 candidates",
        path="see _p3_execute_declared_rc434.ndjson",
        op="the P1 DECLARED-NOT-ENFORCED-at-hop0 population",
        declared="an exception the function's OWN body never raises",
        enforced_by_execution="RAISED, from a callee, in 80 of 82 fired clauses",
        direction="none - the declaration is accurate about observable behaviour",
        ruling="c",
        ruling_justification=(
            "Exactly the shape the brief predicted: the docstring documents an "
            "exception raised by a callee. Documenting observable behaviour at the "
            "API boundary is correct, and is what a caller needs."
        ),
        proposed_type="n/a",
        evidence="_p3 tally ENFORCED=80/82",
        cost="0",
    ),
    dict(
        site_id="T1130-C2",
        surface="docstring (Raises: block)",
        path="docs/srmech/python/srmech/math/cyclic.py:164 and math/primes.py:84",
        op="srmech.math.cyclic.lcm, srmech.math.primes.factor",
        declared="RuntimeError 'NATIVE PATH ONLY'; OverflowError 'unreachable for in-range input'",
        enforced_by_execution=(
            "UNREACHABLE on this host (HAS_NATIVE=False) - BOUNDED, not REFUTED. The "
            "docstrings say so themselves."
        ),
        direction="none",
        ruling="c",
        ruling_justification=(
            "A self-labelled conditional/unreachable clause is honest documentation of "
            "a path this host cannot enter. Deleting it would hide real native-path "
            "behaviour from C-host callers."
        ),
        proposed_type="n/a",
        evidence="_p4(lcm/overflow-clause ENFORCED, factor/overflow-clause NOT_ENFORCED-but-self-declared)",
        cost="0",
    ),
    dict(
        site_id="T1130-C3",
        surface="ToolEntry explanation",
        path="registry entry for srmech.physics.qm.propagators.feynman_scalar_propagator",
        op="feynman_scalar_propagator",
        declared="prose contains 'ZeroDivisionError'",
        enforced_by_execution="ValueError",
        direction="none - the sentence is about the NAIVE ALTERNATIVE, not this op",
        ruling="c",
        ruling_justification=(
            "The sentence reads 'Writing 1j/(k2 - m*m) YOURSELF produces a "
            "ZeroDivisionError' - a contrast with hand-rolling, not a contract. "
            "My prose scanner mis-attributed it; recorded as a false-positive MODE "
            "of prose scanning, not a package defect."
        ),
        proposed_type="n/a",
        evidence="_p7 p6_settle",
        cost="0",
    ),
    dict(
        site_id="T1130-C4",
        surface="ToolEntry explanation x 16",
        path="see _p6 rows NOT_RAISED / PROBE_INADEQUATE_OR_TYPE_MISMATCH",
        op="resolve_path, has_path, kernel_pack, stft, cross_spectral, rfft, render, log, ...",
        declared="an exception named in registry prose",
        enforced_by_execution="my probe fired the WRONG trigger in every case",
        direction="none",
        ruling="c",
        ruling_justification=(
            "_p7 p6_settle prints the actual claim sentence for each: stft claims "
            "ValueError for a 2-D input (I passed []), cross_spectral for MISMATCHED "
            "lengths (I passed two equal empties), kernel_pack for leaf_dim < 52, "
            "has_path for path='verify'. Instrument inadequacy, reported as such."
        ),
        proposed_type="n/a",
        evidence="_p7 p6_settle records",
        cost="0",
    ),
    dict(
        site_id="T1130-LEAD",
        surface="behaviour, not prose",
        path="srmech.cascade.compose.parse_catalog_chains",
        op="parse_catalog_chains",
        declared="ChainSpecError on a schema-version violation",
        enforced_by_execution="AttributeError on malformed TOML input ('[[[')",
        direction="ENFORCED-NOT-DECLARED (a bare AttributeError reaching a public caller)",
        ruling="a",
        ruling_justification=(
            "Not a declared-vs-enforced defect in the strict frame - the docstring "
            "never promised anything here - but an unhandled AttributeError from a "
            "public entry point on malformed input is an ambush. Filed as a LEAD with "
            "its measurement rather than folded into the population."
        ),
        proposed_type="ChainSpecError (adopts the op's own existing error class)",
        evidence="_p6 disagreement row, outcome TYPE_MISMATCH",
        cost="1 guard + 1 test; NOT counted in the T1130 population",
    ),
]


def main() -> int:
    import srmech

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "record": "meta",
                    "task": "#T1130",
                    "srmech_version": srmech.__version__,
                    "srmech_file": srmech.__file__,
                    "filed_claim": "15 mismatches in 4 root-cause families",
                    "measured_defects": 5,
                    "measured_families": 2,
                    "measured_not_a_defect": 4,
                    "leads_outside_population": 1,
                    "projected_registry_delta": 0,
                },
                sort_keys=True,
            )
            + "\n"
        )
        for s in SITES:
            fh.write(json.dumps({"record": "site", **s}, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print(f"wrote {OUT}  sites={len(SITES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
