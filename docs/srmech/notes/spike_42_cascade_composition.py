"""Spike #42 — per-decay cascade composition enumeration.

Apply [[user_stance_primitives_weave_and_thread]] explicitly:
each PDG decay channel is described as a cascade composition of primitive
classes A-N from Spike #24's 14-class vocabulary.

Template borrowed from Spike #38b §5 (caffeine cascade B-J-N-C-D-E-F).

For particle-physics decays, the load-bearing cascade is:
    B (atom-multiset → final-state-multiset; INITIAL particles -> FINAL particles)
  o J (conserved-quantum-number prime-decomposition; L_lepton, B_baryon, Q, S, J)
  o N (rational approximation; branching ratio as best-rational approx of coupling)
  o C (perturbative loop expansion; cascade-streaming)
  o D (channel-selection dispatch; allowed quantum-number routes)
  o E (catalog lookup; PDG-tabulated rules)
  o F (Feynman-diagram template render per channel)
  o L (eigenstructure; mass eigenstates, propagator poles)
  o K (asymptotic-DOF; the epsilon coupling = rate parameter)
  o I (cyclic substrate; phase factors, gauge-group elements)

Per [[feedback_no_privileged_primitive_classes]]: this is cascade-composition
of existing classes, no new class created.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

OUT_DIR = Path(__file__).resolve().parent


def cascade_for(channel: str, classes: List[str], roles: List[str], substrate_note: str) -> Dict:
    return {
        "channel": channel,
        "cascade_classes": classes,
        "cascade_roles": roles,
        "substrate_note": substrate_note,
    }


def main():
    """Build per-decay cascade composition table for pi0 / muon / neutron."""

    records = []

    # ============================================================
    # pi0 decay channels
    # ============================================================
    records.append(cascade_for(
        channel="pi0 -> 2 gamma (leading; 98.823%)",
        classes=["B", "J", "L", "F", "I"],
        roles=[
            "B: initial pi0 (u-ubar - d-dbar isospin singlet); final two photons",
            "J: conserve C-parity (-)^L (pi0 J^PC = 0-+; gamma-gamma allowed)",
            "L: hadronic loop substrate (chiral anomaly diagram); mass eigenstate of pi0",
            "F: chiral-anomaly triangle template (the Adler-Bell-Jackiw template)",
            "I: gauge-group U(1)_EM phase rotation between two photons (cyclic substrate)",
        ],
        substrate_note=(
            "Leading channel = no QED loop suppression beyond the anomaly triangle. "
            "Identity-level: this is the chiral anomaly's algebraic shape, not implementation."
        ),
    ))

    records.append(cascade_for(
        channel="pi0 -> e+ e- gamma (Dalitz; 1.174%)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: same initial; final e+ e- gamma (three particles)",
            "J: conserve all SM quantum numbers (lepton number, charge, parity)",
            "L: anomaly triangle + virtual photon propagator (Class L extended)",
            "F: anomaly template + virtual-photon Dalitz template",
            "K: one alpha-vertex addition (epsilon = alpha/pi rate parameter)",
            "N: rational approx in BR ~ alpha/(2pi) * I_Dalitz; phase-space integral",
            "C: streaming integration over Dalitz Mandelstam variables (s, t)",
        ],
        substrate_note=(
            "First QED radiative correction. epsilon ~ alpha/pi = 2.32e-3 is the rate "
            "on Class K asymptotic-DOF axis. K_1(channel) ~ phase-space factor."
        ),
    ))

    records.append(cascade_for(
        channel="pi0 -> e+ e- e+ e- (double Dalitz; 3.34e-5)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: same initial; final 4 leptons",
            "J: same conservations",
            "L: anomaly triangle + two virtual photon propagators",
            "F: double-Dalitz template (two virtual photons)",
            "K: TWO alpha-vertex additions (epsilon^2 suppression)",
            "N: rational approx as (alpha/pi)^2 * I_2 ; two-pair phase-space",
            "C: nested streaming over two pair-Mandelstams",
        ],
        substrate_note=(
            "Second QED loop level. K_2(channel) ~ 4-5 two-pair phase-space integral. "
            "The eps^k tower dominates; K_k tracks substrate-kinematics."
        ),
    ))

    records.append(cascade_for(
        channel="pi0 -> e+ e- (anomalous; 6.46e-8)",
        classes=["B", "J", "L", "F", "K", "N", "C", "I"],
        roles=[
            "B: same initial; final 2 leptons only",
            "J: conserve all; helicity suppression (J^PC = 0-+ forces m_e factor)",
            "L: loop with virtual photon-pair recombining to e+ e-",
            "F: bubble-diagram template (two-photon loop) with form factor",
            "K: TWO alpha-vertex additions (epsilon^2)",
            "N: rational approx (alpha/pi)^2 * (m_e/m_pi)^2 * log^2 + phase",
            "C: complex-plane streaming over loop momentum",
            "I: helicity-flip phase relations (cyclic substrate at spinor level)",
        ],
        substrate_note=(
            "Helicity-suppressed channel; m_e^2/m_pi^2 ~ 1.43e-5 enters K_3(channel). "
            "Substrate-kinematics factor differs from K_2; same eps^k tower. "
            "Class I emerges because helicity flip is a Z_2 = cyclic-group action."
        ),
    ))

    # ============================================================
    # Muon decay channels
    # ============================================================
    records.append(cascade_for(
        channel="mu -> e nu_e nu_mu (leading; 100% - tiny)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: initial muon; final electron + 2 neutrinos",
            "J: conserve lepton flavor (L_mu, L_e) separately; charge",
            "L: W-boson propagator (heavy gauge-boson eigenstate)",
            "F: V-A current x current template (Michel parameters)",
            "K: weak coupling G_F (NOT alpha here — different rate parameter)",
            "N: rational approx in three-body phase space",
            "C: integration over three-body Lorentz-invariant phase space",
        ],
        substrate_note=(
            "Weak-decay substrate; epsilon parameter is G_F^2 m_mu^5 / 192pi^3. "
            "Different rate-parameter from QED, same eps^k tower structure."
        ),
    ))

    records.append(cascade_for(
        channel="mu -> e nu_e nu_mu gamma (radiative; ~1.4e-2)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: initial muon; final e + 2 nu + gamma",
            "J: same conservations",
            "L: same W-propagator + photon attached",
            "F: leading template + bremsstrahlung attachment",
            "K: one alpha-vertex on top of weak (epsilon = alpha/(2pi) effective)",
            "N: log-enhanced rational approx (IR/coll log factors)",
            "C: streaming with IR-cutoff regularization",
        ],
        substrate_note=(
            "QED-radiative correction to weak decay. Epsilon_K = alpha/(2pi) plus "
            "soft-photon log enhancement. The epsilon spectrum has a log-factor."
        ),
    ))

    records.append(cascade_for(
        channel="mu -> e gamma (LFV; < 4.2e-13 upper limit)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: initial muon; final e + gamma",
            "J: VIOLATES lepton-flavor conservation (SM forbidden at tree)",
            "L: needs BSM heavy state in loop (no SM tree contribution)",
            "F: BSM penguin-like template",
            "K: BSM coupling (UNKNOWN; experimental upper limit only)",
            "N: no SM rational approx; SM prediction ~10^-54",
            "C: BSM loop streaming",
        ],
        substrate_note=(
            "LFV channel = BSM-only; not in eps^k QED tower. The huge gap "
            "(10^11 below radiative) is a SELECTION-RULE break, not a Cauchy step. "
            "Per [[feedback_no_privileged_primitive_classes]], this is Class J "
            "selection-rule violation, not a new class."
        ),
    ))

    # ============================================================
    # Neutron beta decay channels
    # ============================================================
    records.append(cascade_for(
        channel="n -> p e nubar_e (leading; ~99.69%)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: initial neutron (udd); final proton (uud) + e + nubar",
            "J: conserve baryon (B=1->1) and lepton (L=0->-1+1)",
            "L: W-boson propagator (low-energy weak)",
            "F: V-A current template with axial-vector coupling g_A=1.27",
            "K: weak coupling G_F |V_ud|^2 (CKM-element rate parameter)",
            "N: rational approx in phase space + g_A correction",
            "C: streaming over electron energy spectrum",
        ],
        substrate_note=(
            "Different rate-parameter substrate from muon decay: CKM-element |V_ud|^2 "
            "enters multiplicatively. Same eps^k tower structure."
        ),
    ))

    records.append(cascade_for(
        channel="n -> p e nubar_e gamma (radiative; 3.13e-3)",
        classes=["B", "J", "L", "F", "K", "N", "C"],
        roles=[
            "B: initial neutron; final p + e + nubar + gamma",
            "J: same conservations",
            "L: same W-propagator + photon attached to e or p",
            "F: bremsstrahlung template (Sirlin radiative correction)",
            "K: one alpha-vertex on top of weak (Sirlin's eps_rad ~ 0.024)",
            "N: rational approx with log(m_W^2/m_e^2) Sirlin factor",
            "C: streaming with IR cutoff (E_gamma > E_min)",
        ],
        substrate_note=(
            "Sirlin radiative correction. Rate-parameter ~ alpha/pi * log(M_W^2/m_e^2) "
            "is larger than naive alpha/pi due to UV-IR log enhancement. "
            "Same K-axis as muon-radiative; different log factor."
        ),
    ))

    # ============================================================
    # Summary record — the universal cascade-form claim
    # ============================================================
    records.append({
        "kind": "summary_cascade_universal",
        "claim": (
            "Every particle-physics decay channel admits a cascade-composition "
            "description over classes A-N. The eps^k tower (Class K asymptotic-DOF) "
            "is substrate-portable; the K_k(channel) kinematic factor is "
            "substrate-specific (channel-specific). pi0 has K_k from QED phase space "
            "+ helicity; muon and neutron have K_k from weak phase space + Sirlin "
            "logs. Different substrates pick different K_k; the eps^k geometric tower "
            "is the load-bearing universal."
        ),
        "cascade_signature_for_radiative_cascades": "B o J o L o F o K o N o C",
        "cascade_signature_for_selection_violations": "B o J^{!} (J-violation, not Class addition)",
        "alignment_with_spike_41": (
            "Same as Spike #41 finding: c_k = eps^k / k for Kepler (substrate K_k = 1/k) "
            "is one substrate-binding of the same operation. QED's c_k = (alpha/pi)^k * K_k(channel) "
            "is another. The eps^k geometric tower is the load-bearing universal."
        ),
        "no_new_class": (
            "Per [[feedback_no_privileged_primitive_classes]] dissolve-before-promote: "
            "every operation here decomposes into existing A-N. Class B (atom-multiset), "
            "Class J (conservation/factorization), Class L (eigenstructure), Class F "
            "(template), Class K (asymptotic-DOF rate), Class N (rational approx), "
            "Class C (streaming). 7 classes weave. Zero new classes."
        ),
        "load_bearing_class_for_eps_axis": "K (asymptotic-DOF rate parameter)",
        "load_bearing_class_for_substrate_kinematics": "N (rational approx; phase-space integration)",
        "load_bearing_class_for_selection_rules": "J (conservation / prime-factorization)",
    })

    # Print summary
    print("\n=== Spike #42 — Cascade composition per decay channel ===\n")
    for r in records[:-1]:
        ch = r["channel"]
        cs = r["cascade_classes"]
        print(f"\n{ch}:")
        print(f"  Cascade: {' o '.join(cs)}")
        print(f"  Substrate note: {r['substrate_note']}")

    # Save NDJSON
    out_path = OUT_DIR / "spike_42_cascade_composition_records.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"\nEmitted {len(records)} cascade-composition records to {out_path}")


if __name__ == "__main__":
    main()
