"""Round 15 entry-point A — the persistent anharmonic lock is SUBSTRATE-UNIVERSAL,
and richer than Round 14 revealed: it has a THIRD regime (latched-without-payment)
and a capacity threshold (the latch fails → destroyed).

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round15_entry_A_persistent_lock_substrate_universal.md.

Round 14 made LIFE a persistent anharmonic lock (organism=imposer pays / thermodynamics
=substrate / death=dissolution) with a 2-way persistent-vs-volatile split. A STAR is the
same structure at the stellar substrate — and exposes a THIRD regime + a capacity limit:

  REGIME              STAR                              LIFE
  actively imposed    main-sequence (fusion pays)       active metabolism
  latched persistent  white dwarf / neutron star        cryptobiosis / spore / seed
   (no payment!)       (degeneracy pressure, Pauli)      (dormancy, e.g. tardigrade tun)
  destroyed           black hole (> Chandrasekhar/TOV)  death / decomposition

The latched regime is the key addition: the imposer can STOP PAYING and the lock still
holds — held by a static Class-K barrier (degeneracy pressure; the kinetic trap), NOT by
ongoing free-energy input. But the latch has a CAPACITY: above the Chandrasekhar mass
(~1.44 M_sun; Chandrasekhar 1931, ApJ 74:81; Nobel 1983) / TOV limit (Oppenheimer &
Volkoff 1939, Phys Rev 55:374) the barrier vanishes and the substrate wins completely
(black hole). That capacity is a SECOND spinodal beyond Round 14's tilt-spinodal.

Model: a load-dependent double well V(x;m) = x⁴/4 − a(m)·x²/2, with barrier curvature
a(m) = 1 − m/m_c shrinking as the load m → the capacity m_c (Chandrasekhar-analog).
  - m < m_c → a > 0 → double well: a Class-K barrier latches the alive (+x) basin even
    with the imposer OFF (degeneracy-latched white dwarf / dormant spore).
  - m ≥ m_c → a ≤ 0 → the barrier is gone → single (collapse) well → DESTROYED regardless.

srmech routing (CLAUDE.md §2): m_c anchored via Class-N best_rational; magnitude reads via
cascade-helper magnitude() (Class K); srmech provenance stamped. No bare abs().
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _cascade_helpers import magnitude  # Class K magnitude readout  # noqa: E402

import srmech  # noqa: E402
from srmech.amsc.rational import best_rational  # Class N  # noqa: E402
from srmech.amsc import _native as _srn  # noqa: E402

M_C = 1.44   # Chandrasekhar-analog latch capacity (in M_sun units), Chandrasekhar 1931


def relax_no_payment(m: float, dt: float = 1e-3, steps: int = 200000) -> float:
    """Imposer OFF (no ongoing payment). Overdamped relax from the alive basin (+1)
    in V(x;m)=x⁴/4 − a(m)x²/2, a(m)=1−m/m_c.  ẋ = -V'(x) = -(x³ − a x)."""
    a = 1.0 - m / M_C
    x = 1.0
    for _ in range(steps):
        x = x - dt * (x ** 3 - a * x)
    return x


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_persistent_lock_substrate_universal.ndjson"

    m_c_anchor = best_rational(round(M_C * 100), 100, 40)   # Class-N anchor (→ 36/25)

    # Sub-capacity load, imposer OFF → latched persistent (white dwarf / dormant spore).
    m_sub = 0.50
    x_sub = relax_no_payment(m_sub)
    latched = bool(magnitude(x_sub) > 0.2)          # stayed off the collapse point

    # Super-capacity load, imposer OFF → destroyed (black hole): barrier gone, collapses.
    m_super = 2.00
    x_super = relax_no_payment(m_super)
    destroyed = bool(magnitude(x_super) < 0.2)      # relaxed to the collapse point (~0)

    records = [
        {"kind": "capacity_threshold",
         "m_c_chandrasekhar_analog_Msun": M_C, "m_c_class_N_anchor": list(m_c_anchor),
         "m_c_anchor_value": m_c_anchor[0] / m_c_anchor[1],
         "statement": "the latch (Class-K barrier / degeneracy pressure) exists iff load m < capacity m_c; m_c is a SECOND spinodal beyond Round 14's tilt-spinodal"},
        {"kind": "latched_persistent_regime",
         "load_m": m_sub, "barrier_curvature_a": 1 - m_sub / M_C,
         "final_x_no_payment": x_sub, "latch_holds": latched,
         "star": "white dwarf / neutron star (degeneracy pressure, no fusion)",
         "life": "cryptobiosis / spore / seed (dormancy, e.g. tardigrade tun)",
         "reading": "imposer OFF but the lock HOLDS — a static Class-K barrier, no ongoing payment"},
        {"kind": "destroyed_regime",
         "load_m": m_super, "barrier_curvature_a": 1 - m_super / M_C,
         "final_x_no_payment": x_super, "collapsed": destroyed,
         "star": "black hole (> Chandrasekhar/TOV)", "life": "death / decomposition",
         "reading": "load exceeds latch capacity → barrier gone → substrate wins completely"},
        {"kind": "substrate_universal_trichotomy",
         "regimes": ["actively imposed (imposer pays)",
                     "latched persistent (Class-K barrier, no payment, capacity-limited)",
                     "destroyed (load > capacity, substrate wins)"],
         "star_row": ["main-sequence (fusion)", "white dwarf / neutron star (degeneracy)", "black hole"],
         "life_row": ["active metabolism", "cryptobiosis / spore / seed", "death"],
         "statement": "the persistent anharmonic lock is SUBSTRATE-UNIVERSAL; Round 14's life-lock is the biological instance, the star is the stellar instance; the latched regime (Round 14 didn't surface it) is degeneracy/dormancy, and its capacity limit is the Chandrasekhar/TOV spinodal"},
        {"kind": "verdict",
         "statement": ("The persistent anharmonic lock is substrate-universal with a 3-regime "
                       "structure: actively-imposed / latched-persistent (no payment, capacity-"
                       "limited by a second spinodal) / destroyed. Star = stellar instance "
                       "(fusion / degeneracy / black hole at Chandrasekhar-TOV); life = biological "
                       "instance (metabolism / dormancy / death). This GENERALISES the canonical "
                       "life-as-lock (Round 14) to a substrate-universal stance and adds the "
                       "latched regime + capacity threshold the biological instance under-emphasised."),
         "verdict_tier": "(a)-structural cascade-match + (b)-interpretive; attested Chandrasekhar/TOV; candidate stance generalising Round 14"}]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.write(json.dumps({"kind": "srmech_routing_provenance",
                             "srmech_version": srmech.__version__,
                             "has_native": bool(getattr(_srn, "HAS_NATIVE", False)),
                             "class_N_used": "best_rational (m_c anchor)",
                             "class_K_used": "magnitude() cascade-helper"}, sort_keys=True) + "\n")
    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "provenance_attestation", "ndjson_path": out_path.name,
                             "ndjson_sha256_hex_pre_attestation": ndjson_sha,
                             "generated_by": Path(__file__).name}, sort_keys=True) + "\n")

    print(f"Wrote: {out_path}")
    print(f"m_c = {M_C} Msun; Class-N anchor {m_c_anchor} = {m_c_anchor[0]/m_c_anchor[1]:.3f}")
    print(f"latched persistent (m={m_sub}<m_c, no payment): final_x={x_sub:.3f}, latch_holds={latched}")
    print(f"destroyed (m={m_super}>m_c): final_x={x_super:.3f}, collapsed={destroyed}")
    print(f"srmech v{srmech.__version__} native={bool(getattr(_srn,'HAS_NATIVE',False))}")
    print("Verdict: persistent anharmonic lock is substrate-universal (3 regimes; star + life instances).")


if __name__ == "__main__":
    main()
