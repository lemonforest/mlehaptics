"""Always-on C/Python parity smoke test.

Every encoder-touching bridge method must have a C equivalent.

This test is the **scaffolding** that pins that discipline. The
``PARITY_TARGETS`` table below is the spec: every Python bridge
method gets one entry classifying its parity status. Adding a new
encoder-touching method requires either:

  * a paired C entry point (preferred — produces matching output via
    ``backend="c"``), or
  * an explicit ``python_only`` entry justifying why C parity isn't
    needed (pure-Python time scales, validation helpers, etc.)

Status values
=============

  ``parity``       both backends present; outputs must match within
                   tolerance. Test runs both and asserts equality.
  ``python_only``  Python-only by design (pure-Python formula,
                   validation, etc.). Test asserts the Python path
                   works; no C path expected.
  ``tier1_skip``   C port pending in the Tier 1 parity ship. Test
                   skips with the tier marker; flips to ``parity``
                   when the C entry point lands.
  ``tier2_skip``   C port pending in the Tier 2 (HD-state)
                   parity ship. Same flow.

Discipline
==========

  * **Never delete** an entry from this table. Entries flip status as
    work lands; their absence would lose the parity guarantee.
  * **Never silently downgrade** a passing ``parity`` entry to
    ``tier{1,2}_skip``. That hides real regressions. If parity
    breaks, fix the underlying drift, don't reclassify.
  * Skips render in CI as "S" (single-letter), so a glance at the
    pytest summary line shows how many parity targets are still
    pending.

Spec drift detection
====================

The ``test_parity_smoke_spec_covers_bridge_surface`` smoke test
walks every public function in ``ephemerides_spectral.bridge`` and
asserts that the function name appears either in PARITY_TARGETS or
in the explicit allowlist of non-parity-relevant names (validators,
metadata getters, etc.). If you add a new bridge method, this test
forces you to declare its parity status here before CI passes.
"""

from __future__ import annotations

import inspect
import math
from typing import Callable, Dict, Optional

import pytest

from ephemerides_spectral import _native_bip, bridge


# ─────────────────────────────────────────────────────────────────────
# PARITY_TARGETS — the spec.
# ─────────────────────────────────────────────────────────────────────
#
# Each entry maps a bridge function name to a dict describing how to
# exercise it and whether it has a C twin.
#
# Schema:
#   {
#     "status":    one of {"parity", "python_only", "tier1_skip", "tier2_skip"},
#     "kwargs_py": dict of kwargs to call the Python path with,
#     "kwargs_c":  dict for the C path (typically same as kwargs_py
#                  with backend="c" added; only meaningful for
#                  status="parity"),
#     "compare":   callable(py_result, c_result) -> bool, default is
#                  exact-equality on the dict; override for float
#                  tolerance ops,
#     "tier":      Tier number (1, 2) for tier-N-skip statuses; used
#                  in the skip reason,
#     "rationale": one-line explanation for python_only entries,
#   }
#
PARITY_TARGETS: Dict[str, Dict] = {
    # ── Encoder hot path (already at full byte-identical parity) ──────
    "get_system_state": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "backend": "bip"},
        "kwargs_c": {"jd_tdb": 2451545.0, "backend": "c"},
        # phases_uint32 is the byte-identical 38 × uint32 state.
        # `backend` differs (literal "bip" vs "c") which is correct;
        # only compare the encoded state.
        "compare": lambda a, b: a["phases_uint32"] == b["phases_uint32"],
    },
    # ── Tier 1 ports (v0.6.0): C twin shipped ────────────────────────
    # ── v0.8.1 ITN pathway (find-tubes): Python BIP only; C twin queued ─
    "find_itn_pathways": {
        "status": "tier1_skip",
        "tier": 1,
        "kwargs_py": {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 5*365.25,
                      "departure": "terra", "target": "mars",
                      "threshold": 0.05},
    },
    "find_syzygies": {
        "status": "parity",
        "kwargs_py": {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 365.25,
                      "kind": "all", "threshold": 0.05, "backend": "bip"},
        "kwargs_c":  {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 365.25,
                      "kind": "all", "threshold": 0.05, "backend": "c"},
        # Compare candidate list (length + each entry's jd/kind/score)
        # within float tolerance. The `backend` field differs by design.
        "compare": lambda a, b: (
            a["n_candidates"] == b["n_candidates"]
            and all(
                pa["kind"] == pc["kind"]
                and abs(pa["jd_tdb"] - pc["jd_tdb"]) < 1e-9
                and abs(pa["score"] - pc["score"]) < 1e-12
                for pa, pc in zip(a["candidates"], b["candidates"])
            )
        ),
    },
    "get_breathing_modulation": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "pair": ("jupiter", "saturn"),
                      "n_lobes": (5, 2), "backend": "bip"},
        "kwargs_c":  {"jd_tdb": 2451545.0, "pair": ("jupiter", "saturn"),
                      "n_lobes": (5, 2), "backend": "c"},
        # `phase_residue` + `cos_lut_q14` must be byte-identical
        # (integer ops on both sides). `modulation_factor` must agree
        # within float64 ULP.
        "compare": lambda a, b: (
            a["phase_residue"] == b["phase_residue"]
            and a["cos_lut_q14"] == b["cos_lut_q14"]
            and abs(a["modulation_factor"] - b["modulation_factor"]) < 1e-15
        ),
    },
    # ── Tier 2b ports (v0.7.0): HD pipeline in C ─────────────────────
    "get_local_view": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "body": "mars",
                      "lat": 0.0, "lon": 0.0, "backend": "bip", "D": 4096},
        "kwargs_c":  {"jd_tdb": 2451545.0, "body": "mars",
                      "lat": 0.0, "lon": 0.0, "backend": "c", "D": 4096},
        # Compare interleaved state vector within float-tolerance.
        # Float32 round-off + 38-body sum accumulation gives a worst-
        # case ULP order around 1e-5; the tolerance is generous.
        "compare": lambda a, b: (
            len(a["state_interleaved_f32"]) == len(b["state_interleaved_f32"])
            and max(
                abs(x - y) for x, y in zip(
                    a["state_interleaved_f32"], b["state_interleaved_f32"]
                )
            ) < 1e-5
        ),
    },
    "get_eclipse_probability": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "backend": "bip", "D": 4096},
        "kwargs_c":  {"jd_tdb": 2451545.0, "backend": "c", "D": 4096},
        "compare": lambda a, b: abs(a["probability"] - b["probability"]) < 1e-7,
    },
    # ── Pure-Python by design (no C path warranted) ──────────────────
    "get_resolution": {
        "status": "python_only",
        "rationale": "pure analytic; (body, D) → seconds-per-residue, no encoder calls",
        "kwargs_py": {"body": "terra", "D": 65536},
    },
    "get_lunar_phase": {
        "status": "python_only",
        "rationale": "fixed-period synodic + sidereal arithmetic; no encoder calls",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "jd_to_mars_time": {
        "status": "python_only",
        "rationale": "Allison & McEwen 2000 closed-form; no encoder calls",
        "kwargs_py": {"jd_utc": 2451549.5},
    },
    "mars_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_mars_time",
        "kwargs_py": {"msd": 44795.999817},
    },
    "jd_to_sol_uranian_time": {
        "status": "python_only",
        "rationale": "v0.5.4 Sol Uranian Time, sidereal-day arithmetic",
        "kwargs_py": {"jd_tdb": 2454451.0},
    },
    "sol_uranian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranian_time",
        "kwargs_py": {"usd": 0.0},
    },
    # v0.8.0 Sol Symphony Times — pure-Python sidereal/solar arithmetic.
    "jd_to_sol_venus_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Venusian Time (retrograde, sidereal+solar day)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_venus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_venus_time",
        "kwargs_py": {"vsd_solar": 0.0},
    },
    "jd_to_sol_mercury_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Mercurian Time (3:2 spin-orbit resonance)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_mercury_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_mercury_time",
        "kwargs_py": {"mer_sd_solar": 0.0},
    },
    "jd_to_sol_pluto_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Plutonian Time (Pluto-Charon system)",
        "kwargs_py": {"jd_tdb": 2457217.0},
    },
    "sol_pluto_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_pluto_time",
        "kwargs_py": {"psd": 0.0},
    },
    "jd_to_sol_sol_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Sol Time (Carrington rotation system)",
        "kwargs_py": {"jd_tdb": 2398167.4},
    },
    "sol_sol_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_sol_time",
        "kwargs_py": {"crn": 1.0},
    },
    "jd_to_sol_jovian_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Jovian Time (Jupiter System III magnetic-field rotation)",
        "kwargs_py": {"jd_tdb": 2444000.5},
    },
    "sol_jovian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jovian_time",
        "kwargs_py": {"jsd": 0.0},
    },
    "jd_to_sol_saturnian_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Saturnian Time (Cassini-revised System III)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturnian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturnian_time",
        "kwargs_py": {"ssd": 0.0},
    },
    "jd_to_sol_neptunian_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Neptunian Time (Voyager 2 System III)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_neptunian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_neptunian_time",
        "kwargs_py": {"nsd": 0.0},
    },
    "jd_to_sol_terra_time": {
        "status": "python_only",
        "rationale": "v0.9.1 Sol Terra Time (STT) — Terra's surface clock",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_terra_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_terra_time",
        "kwargs_py": {"tsd_solar": 0.0},
    },
    "jd_to_sol_luna_time": {
        "status": "python_only",
        "rationale": "v0.9.1 Sol Luna Time (SLT) — Luna's surface clock; distinct from Sol Lunar Time (which gives synodic+sidereal phase observed from Terra)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_luna_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_luna_time",
        "kwargs_py": {"lsd_solar": 0.0},
    },
    "jd_to_sol_terra_luna_time": {
        "status": "python_only",
        "rationale": "v0.10.0 Sol Terra-Luna Time (STLT) — anchored Lunar time using the synodic month as the natural unit (the 'Terra-Luna' in the name follows the moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention). Default epoch = Meton's 432 BCE summer solstice. First Sol Time member with non-J2000 default anchor. Pure-Python time-scale formula; C twin queued.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_terra_luna_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_terra_luna_time",
        "kwargs_py": {"synodic_count": 0.0},
    },
    # v0.14.0 Sol Moon Times — Galileans (Io / Europa / Ganymede / Callisto).
    # Pure-Python time-scale formulae using each moon's sidereal period
    # from BODIES; no C twin (same status as the rest of the Sol Time
    # series). Tidally locked, so sidereal day = orbital period =
    # rotation period. See test_galilean_sol_moon_times.py.
    "jd_to_sol_jupiter_io_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Io Time (SJIT) — anchored sidereal-cycle count for Io since J2000. Pure-Python time-scale formula; C twin queued. Innermost Galilean; participates in 4:2:1 Laplace resonance with Europa + Ganymede.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_io_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_io_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_europa_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Europa Time (SJET) — anchored sidereal-cycle count for Europa since J2000. Pure-Python time-scale formula; C twin queued.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_europa_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_europa_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_ganymede_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Ganymede Time (SJGT) — anchored sidereal-cycle count for Ganymede since J2000. Pure-Python time-scale formula; C twin queued. Largest moon in the solar system.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_ganymede_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_ganymede_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_callisto_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Callisto Time (SJCT) — anchored sidereal-cycle count for Callisto since J2000. Pure-Python time-scale formula; C twin queued. Outermost Galilean; the only one NOT in the Laplace resonance.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_callisto_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_callisto_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "get_proper_time_rate": {
        "status": "python_only",
        "rationale": "v0.11.0 Sol Proper Time (SPrT) — leading-order GR + orbital kinematic dilation per body. Pure-Python time-scale formula; C twin queued. The same physics as Mercury's existing 43\"/century PN diagonal correction, applied per-body.",
        "kwargs_py": {"body": "terra"},
    },
    "compare_proper_times": {
        "status": "python_only",
        "rationale": "v0.11.0 SPrT — ratio of two bodies' proper-time rates plus 'drift per Earth-year' diagnostic for human comparison.",
        "kwargs_py": {"body_a": "terra", "body_b": "mars"},
    },
    "apply_proper_correction": {
        "status": "python_only",
        "rationale": "v0.11.0 SPrT post-processor — augments a Sol Time bridge result with proper-time-corrected count fields. CLI-layer concern; tested end-to-end via test_sprt.py.",
        "kwargs_py": {"result": {"ok": True, "msd": 1000.0}, "subcommand": "time-mars"},
    },
    "get_kinematic_state": {
        "status": "python_only",
        "rationale": "v0.12.0 Sol Kinematics — per-body mean orbital state from Kepler's third law. Pure-Python time-scale formula; C twin queued. Mirrors chess-spectral's qm_*.py (kinematics) layer.",
        "kwargs_py": {"body": "mars"},
    },
    "get_full_system_state": {
        "status": "python_only",
        "rationale": "v0.12.0 Sol Kinematics — full 38-body roster + system totals (Jupiter L fraction, etc.).",
        "kwargs_py": {},
    },
    "apply_state_correction": {
        "status": "python_only",
        "rationale": "v0.12.0 Sol Kinematics post-processor — augments a Sol Time bridge result with a kinematic_state block via the CLI's --state flag. Mirrors apply_proper_correction.",
        "kwargs_py": {"result": {"ok": True, "msd": 1000.0}, "subcommand": "time-mars"},
    },
    "get_dynamics": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics — system-level KE / PE / total energy + angular momentum partitions. Pure-Python; mirrors chess-spectral's qm_*_dynamics.py *dynamics* layer.",
        "kwargs_py": {},
    },
    "get_force_between": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics — Newtonian gravitational force between two bodies. Validated against the textbook 3.54e22 N Earth-Sun figure.",
        "kwargs_py": {"body_a": "terra", "body_b": "sun"},
    },
    "get_body_energies": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics — per-body KE + PE + total energy budget.",
        "kwargs_py": {"body": "mars"},
    },
    "apply_dynamics_correction": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics post-processor — augments a Sol Time bridge result with a dynamics block (KE/PE/total_E/is_bound) via the CLI's --dynamics flag. Mirrors apply_state_correction and apply_proper_correction.",
        "kwargs_py": {"result": {"ok": True, "msd": 1000.0}, "subcommand": "time-mars"},
    },
    "get_natural_resonance_group": {
        "status": "python_only",
        "rationale": "metadata about the RESONANCES table; pure-Python",
        "kwargs_py": {},
    },
    # ── Patch registry (kept in sync via _mirror_patch_to_native) ────
    # These don't return encoder output directly; they manage state.
    # Their parity is verified end-to-end by get_system_state with
    # patches active (covered by test_native_parity.py + the v0.5.5
    # immolation tests).
    "list_catalog_patches": {
        "status": "python_only",
        "rationale": "metadata over CATALOG/CATALOG_V2 dicts; not encoder I/O",
        "kwargs_py": {},
    },
    "list_active_patches": {
        "status": "python_only",
        "rationale": "registry inspection; both Py + C registries kept in sync via _mirror_patch_to_native",
        "kwargs_py": {},
    },
    "clear_patches": {
        "status": "python_only",
        "rationale": "registry mutation; sync to C via _native_clear_patches",
        "kwargs_py": {},
    },
    # ── Catalog / metadata ───────────────────────────────────────────
    "list_bodies": {
        "status": "python_only",
        "rationale": "metadata over BODIES table; SSOT lives in research/bodies.py",
        "kwargs_py": {},
    },
    "list_kernels": {
        "status": "python_only",
        "rationale": "metadata over KERNELS table",
        "kwargs_py": {},
    },
    "list_lunar_kernels": {
        "status": "python_only",
        "rationale": "metadata over LUNAR_KERNELS table",
        "kwargs_py": {},
    },
    "list_couplings": {
        "status": "python_only",
        "rationale": "metadata over RESONANCES + Laplacian.L_static; not encoder runtime",
        "kwargs_py": {},
    },
    "get_version": {
        "status": "python_only",
        "rationale": "package metadata",
        "kwargs_py": {},
    },
}


# Bridge function names that legitimately do NOT need a parity entry
# (they're plumbing, not encoder ops). Used by the spec-drift smoke.
_NON_PARITY_BRIDGE_NAMES = frozenset({
    # apply_patch / apply_custom_patch are state mutators; their
    # encoder-side correctness is pinned via subsequent
    # get_system_state(backend="c") agreement (covered by
    # test_native_parity + test_runtime_patches).
    "apply_patch",
    "apply_custom_patch",
})


# ─────────────────────────────────────────────────────────────────────
# Driver tests
# ─────────────────────────────────────────────────────────────────────


def _exact_dict_eq(a: Dict, b: Dict) -> bool:
    """Default comparator for parity entries — recursive exact equality."""
    return a == b


@pytest.mark.parametrize("name", sorted(PARITY_TARGETS.keys()))
def test_parity_smoke(name: str) -> None:
    """For each entry in PARITY_TARGETS, exercise its declared parity status."""
    spec = PARITY_TARGETS[name]
    status = spec["status"]
    fn = getattr(bridge, name, None)
    if fn is None:
        pytest.fail(
            f"PARITY_TARGETS lists {name!r} but bridge has no such "
            "attribute; remove the stale entry or restore the function."
        )

    if status == "tier1_skip":
        if not _native_bip.HAS_NATIVE:
            pytest.skip("native library not loaded; tier-1 parity test deferred")
        # Try the Python path; if it works, mark explicit tier-skip.
        # This catches the case where the Python path itself broke.
        kwargs = spec["kwargs_py"]
        out = fn(**kwargs)
        assert out["ok"] is True, (
            f"{name!r} Python path is broken (ok=False): {out.get('error')}; "
            "fix Python first, then port to C."
        )
        pytest.skip(f"tier-1 C port pending; Python path is healthy ({name})")

    if status == "tier2_skip":
        if not _native_bip.HAS_NATIVE:
            pytest.skip("native library not loaded; tier-2 parity test deferred")
        kwargs = spec["kwargs_py"]
        out = fn(**kwargs)
        assert out["ok"] is True, (
            f"{name!r} Python path is broken (ok=False): {out.get('error')}; "
            "fix Python first, then port to C."
        )
        pytest.skip(f"tier-2 C port pending (HD state lift); Python path is healthy ({name})")

    if status == "python_only":
        kwargs = spec["kwargs_py"]
        out = fn(**kwargs)
        # The minimum bar: the call must complete and return ok=True
        # (or be the error-handling Sol-Mars t→JD inverse case which
        # returns positive on success too). All bridge ops in this
        # bucket return ok=True on success.
        assert out.get("ok") is True, (
            f"{name!r} (python_only) returned ok={out.get('ok')!r}: "
            f"{out.get('error')!r}"
        )
        return

    if status == "parity":
        if not _native_bip.HAS_NATIVE:
            pytest.skip("native library not loaded; parity test requires C path")
        py_out = fn(**spec["kwargs_py"])
        c_out = fn(**spec["kwargs_c"])
        assert py_out.get("ok") is True, f"{name!r} BIP path failed: {py_out.get('error')}"
        assert c_out.get("ok") is True, f"{name!r} C path failed: {c_out.get('error')}"
        compare = spec.get("compare", _exact_dict_eq)
        assert compare(py_out, c_out), (
            f"{name!r} parity broken between BIP and C paths.\n"
            f"  BIP: {py_out!r}\n"
            f"  C:   {c_out!r}"
        )
        return

    pytest.fail(f"{name!r} has unknown status {status!r}; fix PARITY_TARGETS schema.")


def test_parity_smoke_spec_covers_bridge_surface() -> None:
    """Drift detection: every public function in bridge must be classified.

    If you add a new bridge method, this test forces you to declare
    its parity status in PARITY_TARGETS (or add it to the explicit
    non-parity allowlist) before CI passes. That keeps the parity
    spec from silently rotting.
    """
    public_fns = [
        name for name, obj in inspect.getmembers(bridge, inspect.isfunction)
        if not name.startswith("_")
        and obj.__module__ == bridge.__name__
    ]
    classified = set(PARITY_TARGETS.keys()) | _NON_PARITY_BRIDGE_NAMES
    unclassified = sorted(set(public_fns) - classified)
    assert not unclassified, (
        f"unclassified bridge functions: {unclassified!r}. Add each to "
        "PARITY_TARGETS (with a parity / python_only / tier1_skip / "
        "tier2_skip status) or to _NON_PARITY_BRIDGE_NAMES with a "
        "rationale. The parity smoke test is the SSOT for which "
        "Python ops have C twins."
    )


def test_parity_smoke_no_orphan_targets() -> None:
    """Reverse drift detection: every PARITY_TARGETS entry must
    correspond to a real bridge function.

    Catches the case where a function got renamed or deleted but the
    PARITY_TARGETS entry stayed.
    """
    public_names = {
        name for name, _ in inspect.getmembers(bridge, inspect.isfunction)
        if not name.startswith("_")
    }
    orphans = sorted(set(PARITY_TARGETS.keys()) - public_names)
    assert not orphans, (
        f"PARITY_TARGETS entries with no corresponding bridge function: "
        f"{orphans!r}. Either restore the function or remove the stale entry."
    )
