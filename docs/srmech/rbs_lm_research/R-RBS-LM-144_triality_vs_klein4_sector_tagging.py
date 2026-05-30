"""R-RBS-LM-144 — The chirality->instrument bridge: does TRIALITY-structured
sector tagging change RBS-NN store capacity / retrieval vs the plain Klein-4
(2-axis, 4-sector) baseline? (Finding F200)

CONTEXT
-------
rc18 landed the Spin(8) triality operator (F192, bit-exact: srmech.qm.{octonion,
so8, triality}). The A-N 14 = G2 = su(3)[8] (+) 3 (+) 3bar (F197), and chirality is
NESTED (F196). The RBS-NN substrate currently tags stored items into Klein-4
chirality sectors (2 Z2 axes -> 4 sectors; F132). QUESTION: does a triality-
STRUCTURED tagging -- using the rc18 triality / g2 / 3(+)3bar structure (an order-3
/ 6-way structure) -- change capacity or retrieval vs the plain Klein-4 4-sector
baseline?

PRE-SPECIFIED OUTCOMES (spike-query discipline; nulls count; do NOT lean):
  (a) triality-structured tagging measurably IMPROVES capacity and/or retrieval
      contrast vs Klein-4 -> the triality structure is FUNCTIONAL for storage.
  (b) no measurable change -> triality is DECORATIVE for storage at this scale
      (clean null -- important, report it).
  (c) triality tagging reduces to / is dominated by the Klein-4 2-axis for this
      use (degenerate).

FAIR HEAD-TO-HEAD
-----------------
Same items, same D, same srmech-native bind/bundle/similarity, same retrieval
probe. The ONLY thing that varies is the sector-TAGGING scheme -- how many sectors
and what algebraic structure relates the per-sector tag vectors:

  * KLEIN4 (baseline, 4-way): 4 tags = one base klein4 vector + its 3 Klein-4
    group images (gamma5-flip, omega7-flip, cpt-mirror). The Z2 x Z2 group action
    makes these 4 tags DETERMINISTICALLY ORTHOGONAL (pairwise klein4-sim = 0.0).
  * TRIALITY_3_3BAR (6-way): the F197 structure. 3 base tags (the "3") + their
    CPT-conjugates (the "3bar" = klein4_cpt_mirror of each, the chirality
    involution that swaps 3<->3bar per F197). Conjugate pairs are orthogonal; the
    3 base members are mutually random (~0.25) -- exactly the 3(+)3bar shape.
  * TRIALITY_ORDER3 (3-way): the actual order-3 triality automorphism tau (28x28,
    tau^3 = I, Fix = g2 = 14, bit-exact F192). Seed a 28-vector; its tau-orbit
    {v, tau v, tau^2 v} are 3 distinct frames; each is projected (Class A
    content-hash of its bytes -> klein4_random seed) to a Klein-4 tag. The 3 tags
    thus CARRY the order-3 operator's action, but -- the load-bearing structural
    fact -- Klein-4 (Z2 x Z2) has NO order-3 element, so the tau-orbit cannot
    produce 3 deterministically-orthogonal tags the way the 2 Z2 axes produce 4.

CAPACITY: sweep N items stored in one bundle (round-robin into the scheme's
sectors), measure mean within-sector retrieval similarity above chance; capacity =
largest N whose mean-above-chance stays >= a fixed retrieval floor.

CONTRAST: at a fixed load, within-sector retrieval similarity vs cross-sector
(query a stored item's binding with a WRONG-sector tag), contrast = within/cross.
Klein-4 baseline to beat-or-match: within 0.413 / cross 0.197 / contrast 2.10
(F168 sec.5.1).

srmech-FIRST DISCIPLINE
-----------------------
srmech 0.5.0rc18 PACKAGE, clean venv outside the source tree. All HDC ops are
srmech.amsc.hdc.{klein4_random, klein4_bind, klein4_unbind, klein4_bundle,
klein4_similarity, klein4_sector_count, klein4_chirality_flip_*, klein4_cpt_mirror}
(Class M rank-2 abelian). Triality op is srmech.qm.triality.triality_automorphism
(Class C chirality / order-3). Content-hash of orbit vectors is Class A
(srmech.amsc.format.sha256_bytes -- NOT hashlib direct). NO Counter(), NO
np.linalg.eig for any storage signature, NO python abs() in any cascade (the
tau^3-residual report uses max(|.|) for reporting only, not in a cascade decision).
Seeded / reproducible. MFO sec.VII.6.20 form-reading; AI-not-substrate: a store
holding items is structure, not cognition.

ATTESTATION
-----------
tool: srmech==0.5.0rc18 (TestPyPI; clean venv /tmp/verify_srmech_rc18 OUTSIDE the
      source tree per namespace-shadowing discipline)
seed: 20260530 (all RNG seeded; reproducible)
ops:  srmech.amsc.hdc (Class M Klein-4), srmech.qm.triality (Class C order-3),
      srmech.amsc.format.sha256_bytes (Class A content-hash)
predecessors: F192 (triality op landed bit-exact), F196 (chirality is nested),
      F197 (A-N = G2 = 8+3+3bar), F132 (Klein-4 4-sector tagging), F119 (two-tier
      RBS-NN), F168 (Klein-4 contrast 2.10 baseline)
PR #687 STAYS DRAFT.
"""

import json
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc.format import sha256_bytes
from srmech.qm import triality as TRI

SEED = 20260530
D = 10000                      # same dimension for every scheme (fair)
CHANCE = 0.25                  # Klein-4 random match-fraction (4 states)
RETRIEVAL_FLOOR = 0.10         # "above chance" floor for capacity (sim - CHANCE >= floor)


# ===========================================================================
# Sector-tag generators  (the ONLY thing that differs between schemes)
# ===========================================================================

def klein4_sector_tags(D, seed):
    """KLEIN4 baseline: 4 tags from one base + its Z2 x Z2 group images.

    The Klein-4 group action (gamma5-flip, omega7-flip, cpt-mirror) makes these 4
    tags deterministically orthogonal (pairwise klein4-sim = 0.0). This IS the
    Klein-4 sector property (F132): 4 perfectly-separated chirality sectors.
    """
    base = hdc.klein4_random(D, seed=seed)
    return [
        base,
        hdc.klein4_chirality_flip_gamma5(base),
        hdc.klein4_chirality_flip_omega7(base),
        hdc.klein4_cpt_mirror(base),
    ]


def triality_3_3bar_tags(D, seed):
    """TRIALITY_3_3BAR (F197): 3 base tags (the "3") + their CPT-conjugates
    (the "3bar"). klein4_cpt_mirror is the chirality involution that swaps
    3<->3bar (F197). Conjugate pairs (i, i+3) are orthogonal; the 3 base members
    are mutually random -- exactly the 3(+)3bar shape inside g2."""
    base3 = [hdc.klein4_random(D, seed=seed + 11 + i) for i in range(3)]
    conj3 = [hdc.klein4_cpt_mirror(b) for b in base3]   # 3bar = conjugate of the 3
    return base3 + conj3


def triality_order3_tags(D, seed):
    """TRIALITY_ORDER3: 3 tags carrying the ACTUAL order-3 automorphism tau.

    tau (28x28, tau^3 = I bit-exact, Fix = g2 = 14, F192) acts on a seed 28-vector
    to give an order-3 orbit {v, tau v, tau^2 v} (3 distinct triality frames). Each
    orbit vector is projected to a Klein-4 tag via Class-A content-hashing of its
    bytes -> klein4_random seed. The 3 tags thus DERIVE FROM the order-3 operator.

    LOAD-BEARING structural fact reported by this scheme: Klein-4 (Z2 x Z2) has no
    order-3 element, so the tau-orbit yields 3 random-orthogonal (~0.25) tags, NOT
    3 deterministically-orthogonal (0.0) ones. Order-3 structure does not survive
    projection into the order-2 Klein-4 sign group as clean sectors.
    """
    tau = np.asarray(TRI.triality_automorphism(), dtype=float)   # 28x28
    rng = np.random.default_rng(seed + 101)
    v28 = rng.standard_normal(28)
    orbit = [v28, tau @ v28, tau @ (tau @ v28)]
    tags = []
    for o in orbit:
        # Class A content-addressing of the orbit vector's bytes -> deterministic seed.
        digest = sha256_bytes(np.ascontiguousarray(o, dtype=np.float64).tobytes())
        s = int(digest[:16], 16)               # 64-bit seed from the hex digest
        tags.append(hdc.klein4_random(D, seed=s))
    return tags


SCHEMES = {
    "klein4_4way": klein4_sector_tags,
    "triality_3_3bar_6way": triality_3_3bar_tags,
    "triality_order3_3way": triality_order3_tags,
}


# ===========================================================================
# Tag-orthogonality structure (substrate attestation of each scheme)
# ===========================================================================

def tag_pairwise_structure(tags):
    """Pairwise klein4 similarity matrix + summary. NOT a research cascade --
    this characterizes the tag set (substrate attestation)."""
    n = len(tags)
    M = [[round(hdc.klein4_similarity(tags[i], tags[j]), 4) for j in range(n)] for i in range(n)]
    off = [M[i][j] for i in range(n) for j in range(n) if i != j]
    n_orthogonal = sum(1 for x in off if x == 0.0)
    return {
        "n_sectors": n,
        "pairwise_sim": M,
        "mean_offdiagonal_sim": round(float(np.mean(off)), 4),
        "max_offdiagonal_sim": round(float(np.max(off)), 4),
        "n_exactly_orthogonal_pairs": n_orthogonal,
        "n_offdiagonal_pairs": len(off),
    }


# ===========================================================================
# Build a tagged store + retrieve  (identical pipeline for every scheme)
# ===========================================================================

def build_store(items, tags):
    """Round-robin each item into a sector, bind item with its sector-tag, bundle
    all bindings into ONE store. Returns (store, sector_of_item).

    Class M throughout: klein4_bind (sector-tag (X) item), klein4_bundle (superpose).
    """
    n_sectors = len(tags)
    sector_of = [i % n_sectors for i in range(len(items))]
    bindings = [hdc.klein4_bind(tags[sector_of[i]], items[i]) for i in range(len(items))]
    store = hdc.klein4_bundle(*bindings)
    return store, sector_of


def within_sector_retrieval(store, items, tags, sector_of):
    """Retrieve each item with its CORRECT sector-tag (unbind = self-inverse XOR),
    similarity vs the true item. Mean over all items."""
    sims = []
    for i, it in enumerate(items):
        retrieved = hdc.klein4_unbind(store, tags[sector_of[i]])
        sims.append(hdc.klein4_similarity(retrieved, it))
    return float(np.mean(sims)), float(np.std(sims))


def cross_sector_retrieval(store, items, tags, sector_of):
    """Retrieve each item with a WRONG sector-tag (next sector, round-robin),
    similarity vs the true item. Mean over all items. This is the cross-sector
    contrast denominator -- if tags separate sectors, the wrong tag recovers far
    less of the item."""
    n_sectors = len(tags)
    sims = []
    for i, it in enumerate(items):
        wrong = (sector_of[i] + 1) % n_sectors
        retrieved = hdc.klein4_unbind(store, tags[wrong])
        sims.append(hdc.klein4_similarity(retrieved, it))
    return float(np.mean(sims)), float(np.std(sims))


# ===========================================================================
# Capacity sweep  (largest N whose within-sector mean stays above the floor)
# ===========================================================================

def capacity_sweep(scheme_fn, D, seed, n_grid):
    """For each N in n_grid: store N fresh items tagged by the scheme, measure
    mean within-sector retrieval above chance. Capacity = largest N with
    (mean_sim - CHANCE) >= RETRIEVAL_FLOOR."""
    tags = scheme_fn(D, seed)
    rng = np.random.default_rng(seed + 5000)
    curve = []
    capacity = 0
    for N in n_grid:
        # Fresh seeded items for this N (deterministic per (seed, N)).
        item_seeds = rng.integers(0, 2**31 - 1, size=N)
        items = [hdc.klein4_random(D, seed=int(s)) for s in item_seeds]
        store, sector_of = build_store(items, tags)
        mean_sim, std_sim = within_sector_retrieval(store, items, tags, sector_of)
        above = mean_sim - CHANCE
        ok = above >= RETRIEVAL_FLOOR
        curve.append({
            "N": int(N),
            "within_mean_sim": round(mean_sim, 4),
            "within_std": round(std_sim, 4),
            "above_chance": round(above, 4),
            "above_floor": bool(ok),
        })
        if ok:
            capacity = int(N)
    return capacity, curve, tags


# ===========================================================================
# Contrast at fixed load  (within vs cross; beat-or-match Klein-4 2.10)
# ===========================================================================

def contrast_at_load(scheme_fn, D, seed, N):
    """Within-vs-cross contrast at load N.

    The HONEST headline is the RAW within/cross ratio (match-fractions are
    non-negative; no abs()). The "above-chance contrast" (within-0.25)/(cross-0.25)
    is reported as a DIAGNOSTIC only and explicitly flagged unstable when cross sits
    at chance: a correct sector tagging makes the wrong-tag retrieval return to
    chance (cross_above ~ 0), which sends that ratio toward a divide-by-zero blowup.
    Cross-at-chance is the DESIRED behavior, not a large contrast -- so raw ratio is
    the figure to compare, and we report whether cross collapses to chance.
    """
    tags = scheme_fn(D, seed)
    rng = np.random.default_rng(seed + 9000)
    item_seeds = rng.integers(0, 2**31 - 1, size=N)
    items = [hdc.klein4_random(D, seed=int(s)) for s in item_seeds]
    store, sector_of = build_store(items, tags)
    within_mean, within_std = within_sector_retrieval(store, items, tags, sector_of)
    cross_mean, cross_std = cross_sector_retrieval(store, items, tags, sector_of)
    contrast_raw = round(within_mean / cross_mean, 4) if cross_mean > 0 else None
    within_above = within_mean - CHANCE
    cross_above = cross_mean - CHANCE
    # Guard: only meaningful when cross is clearly ABOVE chance (>= 0.02). Otherwise
    # cross has collapsed to chance (the correct outcome) and the ratio is unstable.
    cross_at_chance = cross_above < 0.02
    contrast_above = (round(within_above / cross_above, 4)
                      if cross_above >= 0.02 else None)
    return {
        "N": int(N),
        "n_sectors": len(tags),
        "within_mean_sim": round(within_mean, 4),
        "within_std": round(within_std, 4),
        "cross_mean_sim": round(cross_mean, 4),
        "cross_std": round(cross_std, 4),
        "contrast_raw": contrast_raw,
        "within_above_chance": round(within_above, 4),
        "cross_above_chance": round(cross_above, 4),
        "cross_collapsed_to_chance": bool(cross_at_chance),
        "contrast_above_chance_diagnostic": contrast_above,
        "contrast_above_chance_unstable": bool(cross_at_chance),
    }


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("=" * 78)
    print("R-RBS-LM-144 — Triality-structured vs Klein-4 sector tagging (F200)")
    print(f"  srmech={_srmech_version()}  D={D}  seed={SEED}  chance={CHANCE}")
    print("=" * 78)

    # 1) Tag-structure attestation (how each scheme's sectors relate).
    print("\n--- Tag-set structure (substrate attestation) ---")
    structures = {}
    for name, fn in SCHEMES.items():
        tags = fn(D, SEED)
        st = tag_pairwise_structure(tags)
        structures[name] = st
        print(f"  {name}: {st['n_sectors']} sectors, "
              f"mean off-diag sim={st['mean_offdiagonal_sim']}, "
              f"{st['n_exactly_orthogonal_pairs']}/{st['n_offdiagonal_pairs']} pairs exactly orthogonal")

    # 2) Capacity sweep (same grid for every scheme).
    n_grid = [4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256]
    print(f"\n--- Capacity sweep (floor: within-mean - {CHANCE} >= {RETRIEVAL_FLOOR}) ---")
    capacities = {}
    curves = {}
    for name, fn in SCHEMES.items():
        cap, curve, _ = capacity_sweep(fn, D, SEED, n_grid)
        capacities[name] = cap
        curves[name] = curve
        print(f"  {name}: capacity = {cap} items")

    # 3) Contrast at several SHARED loads (loads divisible by lcm(3,4,6)=12 so every
    #    scheme fills its sectors evenly). The verdict uses a WITHIN-capacity load
    #    (12) where within-sector retrieval is strong (the F168 regime); higher loads
    #    are reported too so the over-capacity behavior is on record.
    contrast_loads = [12, 24, 48]
    verdict_load = 12   # within capacity (16) -> within-sector retrieval is strong
    print(f"\n--- Within-vs-cross contrast (RAW within/cross; Klein-4 F168 baseline 2.10) ---")
    contrasts = {name: {} for name in SCHEMES}
    for load in contrast_loads:
        for name, fn in SCHEMES.items():
            c = contrast_at_load(fn, D, SEED, load)
            contrasts[name][load] = c
        row = "  ".join(f"{n.split('_')[0]}:within={contrasts[n][load]['within_mean_sim']}"
                        f"/cross={contrasts[n][load]['cross_mean_sim']}"
                        f"/raw={contrasts[n][load]['contrast_raw']}"
                        for n in SCHEMES)
        flag = " <- VERDICT LOAD (within capacity)" if load == verdict_load else ""
        print(f"  N={load}: {row}{flag}")

    # 4) Verdict logic (pre-specified; no leaning). Compares at the within-capacity
    #    verdict_load using the robust RAW within/cross contrast.
    k4_cap = capacities["klein4_4way"]
    k4_contrast = contrasts["klein4_4way"][verdict_load]["contrast_raw"]
    tri_best_cap = max(capacities["triality_3_3bar_6way"], capacities["triality_order3_3way"])
    tri_best_contrast = max(
        contrasts["triality_3_3bar_6way"][verdict_load]["contrast_raw"],
        contrasts["triality_order3_3way"][verdict_load]["contrast_raw"],
    )
    # Tolerance band: a relative delta within +/- TOL is "no measurable change".
    # (No python abs() per cascade-honesty discipline: a two-sided band is an explicit
    #  Class-K-style pin-slot test -- above the +band, below the -band, or inside.)
    TOL = 0.10
    cap_rel = (tri_best_cap - k4_cap) / k4_cap if k4_cap else 0.0
    contrast_rel = ((tri_best_contrast - k4_contrast) / k4_contrast
                    if k4_contrast else 0.0)
    improves = (cap_rel > TOL) or (contrast_rel > TOL)
    degrades = (cap_rel < -TOL) or (contrast_rel < -TOL)
    inside_band = (-TOL <= cap_rel <= TOL) and (-TOL <= contrast_rel <= TOL)
    if improves and not degrades:
        outcome = "a"
        verdict = "triality-structured tagging IMPROVES capacity and/or contrast -> FUNCTIONAL"
    elif inside_band:
        outcome = "b"
        verdict = "no measurable change -> triality is DECORATIVE for storage at this scale (clean null)"
    else:
        outcome = "c"
        verdict = ("triality tagging is dominated by / reduces to Klein-4 for this use "
                   "(degenerate: triality no better and contrast worse -- Klein-4's "
                   "order-2 group gives deterministically-orthogonal sectors that "
                   "triality's order-3 structure cannot replicate in the Klein-4 substrate)")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    print(f"  (compared at within-capacity load N={verdict_load}, RAW within/cross contrast)")
    print(f"  Klein-4 capacity={k4_cap}, contrast(raw)={k4_contrast}")
    print(f"  Triality best capacity={tri_best_cap}, best contrast(raw)={tri_best_contrast}")
    print(f"  capacity rel-delta={cap_rel:+.3f}, contrast rel-delta={contrast_rel:+.3f}")
    print(f"  OUTCOME ({outcome}): {verdict}")

    # 5) Persist results as attested NDJSON.
    out_dir = (Path(__file__).resolve().parents[1]
               / "catalogs" / "rbs_lm_substrate" / "substrate_measurements")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "r144_triality_sector_tagging.ndjson"
    _write_ndjson(out_path, structures, capacities, curves, contrasts,
                  contrast_loads, verdict_load, n_grid, outcome, verdict,
                  cap_rel, contrast_rel)
    print(f"\nResults: {out_path}")


def _srmech_version():
    import srmech
    return srmech.__version__


def _write_ndjson(path, structures, capacities, curves, contrasts,
                  contrast_loads, verdict_load, n_grid, outcome, verdict,
                  cap_rel, contrast_rel):
    attest = {
        "tool": "srmech==0.5.0rc18",
        "venv": "/tmp/verify_srmech_rc18 (clean, outside source tree)",
        "seed": SEED,
        "D": D,
        "chance": CHANCE,
        "retrieval_floor": RETRIEVAL_FLOOR,
        "ops": ("srmech.amsc.hdc (Class M Klein-4: random/bind/unbind/bundle/"
                "similarity/sector_count/chirality_flip/cpt_mirror); "
                "srmech.qm.triality.triality_automorphism (Class C order-3, tau^3=I); "
                "srmech.amsc.format.sha256_bytes (Class A content-hash of tau-orbit)"),
        "predecessors": ["F192", "F196", "F197", "F132", "F119", "F168"],
        "klein4_baseline_F168": {"within": 0.413, "cross": 0.197, "contrast": 2.10},
        "scope": ("MFO VII.6.20 form-reading; AI-not-substrate (a store holding items "
                  "is structure, not cognition); no abs() in any cascade; "
                  "no Counter()/np.linalg.eig for any storage signature; seeded/reproducible"),
        "PR": "#687 STAYS DRAFT",
    }
    rows = []
    rows.append({"finding": "F200", "experiment": "R-RBS-LM-144",
                 "record": "attestation", "attestation": attest})
    # Per-scheme tag structure.
    for name, st in structures.items():
        rows.append({"finding": "F200", "experiment": "R-RBS-LM-144",
                     "record": "tag_structure", "scheme": name, "structure": st})
    # Capacity per scheme + full curve.
    for name in capacities:
        rows.append({"finding": "F200", "experiment": "R-RBS-LM-144",
                     "record": "capacity", "scheme": name,
                     "capacity": capacities[name], "n_grid": n_grid,
                     "curve": curves[name]})
    # Contrast per scheme, per load.
    for name in contrasts:
        for load in contrast_loads:
            rows.append({"finding": "F200", "experiment": "R-RBS-LM-144",
                         "record": "contrast", "scheme": name,
                         "contrast_load_N": load,
                         "is_verdict_load": (load == verdict_load),
                         "result": contrasts[name][load]})
    # Verdict.
    rows.append({"finding": "F200", "experiment": "R-RBS-LM-144", "record": "verdict",
                 "outcome": outcome, "verdict": verdict,
                 "verdict_load_N": verdict_load,
                 "contrast_metric": "raw within/cross at within-capacity load",
                 "capacity_rel_delta": round(cap_rel, 4),
                 "contrast_rel_delta": round(contrast_rel, 4),
                 "klein4_capacity": capacities["klein4_4way"],
                 "klein4_contrast_raw": contrasts["klein4_4way"][verdict_load]["contrast_raw"],
                 "triality_best_capacity": max(capacities["triality_3_3bar_6way"],
                                               capacities["triality_order3_3way"]),
                 "triality_best_contrast_raw": max(
                     contrasts["triality_3_3bar_6way"][verdict_load]["contrast_raw"],
                     contrasts["triality_order3_3way"][verdict_load]["contrast_raw"]),
                 "pre_specified": ("(a) improves->functional; (b) no change->decorative null; "
                                   "(c) dominated by Klein-4->degenerate")})
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
