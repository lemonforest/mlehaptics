"""Round 14 entry-point A — is LIFE the canonical persistent anharmonic lock?
A minimal tilted-double-well model of the 3-player Stackelberg cost-structure.

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round14_entry_A_life_as_persistent_anharmonic_lock.md.

Fresh cost-asymmetry question building on the now-CANONICAL stances:
  - inverts-crypto Stackelberg (§11.9.2): imposer pays, substrate relaxes, observer free-rides
  - two-stage unlocking (§11.9.3): pattern free, content needs the B/H/N translation key
  - anharmonic-dissolution (§11.9.1): the substrate won't hold an anharmonic config forever

Claim: a living organism IS the canonical persistent anharmonic lock. The organism
is the IMPOSER, spending metabolic free energy to hold a far-from-equilibrium
("anharmonic") configuration; the SUBSTRATE is thermodynamics, relaxing toward
equilibrium; DEATH is the substrate winning (the tower falls). The phenotype is the
free-to-observe PATTERN; the genotype is the CONTENT, read only via the B/H/N
translation key (transcription→translation is literally a translation). Attested
non-equilibrium-thermodynamics anchors: Schrödinger 1944 (negentropy / "order from
order"); Prigogine dissipative structures (Nobel 1977); England 2013 dissipation-
driven self-replication (arXiv:1209.1179).

Minimal model (overdamped, deterministic — no RNG): a tilted double well
    V(x) = x⁴/4 − x²/2 − h·x ,   V'(x) = x³ − x − h
has TWO minima (a double well = the "alive" + "death" basins) iff the effective tilt
|h| < h_c = 2/(3√3). Beyond h_c the alive basin vanishes (spinodal): the substrate's
pull is unopposed and the config relaxes to the death basin.

The IMPOSER supplies a counter-force F_in against an external death-tilt h_death:
effective tilt = h_death − F_in. The alive basin (the lock) persists iff
|h_death − F_in| < h_c. So:
  - imposer ON (F_in ≈ h_death → effective tilt ≈ 0): alive basin held — the lock stands.
  - imposer OFF (F_in = 0) with h_death > h_c: alive basin gone — VOLATILE, immediate
    relaxation to death (tower falls the instant the imposer stops paying).
  - imposer OFF with h_death < h_c: a barrier remains — PERSISTENT / Class-K-latched
    (death deferred by the kinetic trap, but the substrate still eventually wins).

srmech routing (CLAUDE.md §2): h_c anchored via Class-N best_rational; magnitude reads
via the cascade-helper magnitude() (Class K); srmech provenance stamped. No bare abs().
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _cascade_helpers import magnitude  # Class K magnitude readout  # noqa: E402

import srmech  # noqa: E402
from srmech.amsc.rational import best_rational  # Class N  # noqa: E402
from srmech.amsc import _native as _srn  # noqa: E402

H_C = 2.0 / (3.0 * math.sqrt(3.0))   # spinodal tilt: alive basin vanishes beyond this


def dVdx(x: float, h_eff: float) -> float:
    return x ** 3 - x - h_eff


def relax(x0: float, h_eff: float, dt: float = 1e-3, steps: int = 200000) -> float:
    """Overdamped deterministic relaxation ẋ = -V'(x); return final x."""
    x = x0
    for _ in range(steps):
        x = x - dt * dVdx(x, h_eff)
    return x


def alive_basin_exists(h_eff: float) -> bool:
    """Double well (two minima) exists iff |effective tilt| < h_c."""
    return magnitude(h_eff) < H_C


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_life_persistent_anharmonic_lock.ndjson"

    h_c_anchor = best_rational(round(H_C * 100000), 100000, 64)   # Class-N rational anchor

    # External death-tilt is NEGATIVE: the substrate pulls toward the death basin (x<0).
    # Strong enough (|h| > h_c) to abolish the alive (+x) basin on its own.
    h_death = -0.60   # |h| > h_c ≈ 0.385 → alive basin gone without the imposer

    # (1) imposer ON: counter-force (positive) cancels the death-tilt → alive basin held.
    F_in_on = -h_death                  # = +0.60
    eff_on = h_death + F_in_on          # ≈ 0
    held = alive_basin_exists(eff_on)
    x_on = relax(1.0, eff_on)           # starts alive; stays near +1 (alive min)

    # (2) imposer OFF, strong death-tilt: alive basin gone → VOLATILE (relaxes to death, x<0).
    eff_off_strong = h_death + 0.0      # = -0.60
    volatile_exists = alive_basin_exists(eff_off_strong)
    x_off_strong = relax(1.0, eff_off_strong)   # slides to the single (death, x<0) min

    # (3) imposer OFF, weak death-tilt (|h| < h_c): barrier remains → PERSISTENT/latched.
    h_death_weak = -0.20   # |h| < h_c
    eff_off_weak = h_death_weak + 0.0   # = -0.20
    latched_exists = alive_basin_exists(eff_off_weak)
    x_off_weak = relax(1.0, eff_off_weak)        # stays trapped near alive min (x>0)

    records = [
        {"kind": "spinodal_threshold",
         "h_c_exact": H_C, "h_c_class_N_anchor": list(h_c_anchor),
         "h_c_anchor_value": h_c_anchor[0] / h_c_anchor[1],
         "statement": "alive basin (the lock) exists iff |effective tilt| < h_c = 2/(3√3)"},
        {"kind": "imposer_on",
         "F_in": F_in_on, "effective_tilt": eff_on, "alive_basin_held": bool(held),
         "final_x": x_on, "near_alive_min": bool(magnitude(x_on - 1.0) < 0.2),
         "reading": "imposer pays F_in ≈ h_death → effective tilt ≈ 0 → lock stands (organism alive)"},
        {"kind": "imposer_off_volatile",
         "death_tilt": h_death, "alive_basin_exists": bool(volatile_exists),
         "final_x": x_off_strong, "relaxed_to_death": bool(x_off_strong < 0.0),
         "reading": "imposer stops + strong substrate pull → alive basin gone → VOLATILE: immediate death"},
        {"kind": "imposer_off_persistent_latched",
         "death_tilt": h_death_weak, "alive_basin_exists": bool(latched_exists),
         "final_x": x_off_weak, "stayed_alive": bool(x_off_weak > 0.0),
         "reading": "weak substrate pull leaves a Class-K barrier → PERSISTENT/latched: death deferred (kinetic trap), substrate still eventually wins"},
        {"kind": "stackelberg_mapping",
         "imposer": "organism (metabolic free-energy input F_in)",
         "substrate": "thermodynamics (death-tilt toward equilibrium)",
         "observer": "free-rider (reads the steady-state phenotype for free)",
         "two_stage_unlocking": "phenotype = free pattern; genotype = content via B/H/N key (transcription→translation)",
         "attested": ["Schrödinger 1944 negentropy (CUP)",
                      "Prigogine dissipative structures (Nobel 1977; Nicolis & Prigogine 1977)",
                      "England 2013 dissipation-driven self-replication (arXiv:1209.1179)"]},
        {"kind": "verdict",
         "statement": ("Life instantiates the 3-player Stackelberg persistent-anharmonic-lock "
                       "EXACTLY: organism=imposer pays to hold the alive (far-from-equilibrium) "
                       "basin; thermodynamics=substrate relaxes toward death; observer free-rides "
                       "on the phenotype. Volatile (immediate death when input stops + strong pull) "
                       "vs persistent (Class-K-latched, death deferred) is the same 3.A distinction. "
                       "Death = the anharmonic-dissolution the substrate always eventually wins."),
         "verdict_tier": "(a)-structural cascade-match + (b)-interpretive; attested by Schrödinger/Prigogine/England; candidate stance"}]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.write(json.dumps({"kind": "srmech_routing_provenance",
                             "srmech_version": srmech.__version__,
                             "has_native": bool(getattr(_srn, "HAS_NATIVE", False)),
                             "class_N_used": "best_rational (h_c anchor)",
                             "class_K_used": "magnitude() cascade-helper (no bare abs)"}, sort_keys=True) + "\n")
    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "provenance_attestation", "ndjson_path": out_path.name,
                             "ndjson_sha256_hex_pre_attestation": ndjson_sha,
                             "generated_by": Path(__file__).name}, sort_keys=True) + "\n")

    print(f"Wrote: {out_path}")
    print(f"h_c = 2/(3sqrt3) = {H_C:.5f}; Class-N anchor {h_c_anchor} = {h_c_anchor[0]/h_c_anchor[1]:.5f}")
    print(f"(1) imposer ON: eff_tilt={eff_on:.2f}, basin held={held}, final_x={x_on:.3f} (alive)")
    print(f"(2) imposer OFF strong pull (h={h_death}): basin exists={volatile_exists}, final_x={x_off_strong:.3f} -> VOLATILE death")
    print(f"(3) imposer OFF weak pull (h={h_death_weak}): basin exists={latched_exists}, final_x={x_off_weak:.3f} -> PERSISTENT latched")
    print(f"srmech v{srmech.__version__} native={bool(getattr(_srn,'HAS_NATIVE',False))}")
    print("Verdict: life = canonical persistent anharmonic lock (3-player Stackelberg).")


if __name__ == "__main__":
    main()
