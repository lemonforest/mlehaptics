"""R-RBS-LM-105 — Sweep C: plasticity dynamics + Pareto frontiers

Resolves STALE items: 12 (D vs N Pareto), 18 (Klein-4 under decay),
19 (decay-recovery dynamics / rehearsal), 20 (D/N/decay Pareto),
21 (noise-vs-decay distinction), 24 (polar+Klein-4 hybrid), 27 (4-way at signal level).
"""
import json
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


SECTOR_CPT_MIRROR = {0: 3, 1: 2, 2: 1, 3: 0}


def random_baseline_klein4(D, rng, N=50):
    sims = []
    for _ in range(N):
        a = hdc.klein4_random(D, rng)
        b = hdc.klein4_random(D, rng)
        sims.append(float(hdc.klein4_similarity(a, b)))
    return float(np.mean(sims))


def random_baseline_polar(D, rng, N=50):
    sims = []
    for _ in range(N):
        a = hdc.polar_random(D, rng)
        b = hdc.polar_random(D, rng)
        sims.append(float(hdc.polar_similarity(a, b)))
    return float(np.mean(sims))


# === Item 18: Klein-4 under decay ===
def item_18_klein4_decay(D, N, decay_fracs, rng):
    """F141-style decay test but on klein-4 instead of polar.

    For klein-4, decay means setting positions to state 0 (the identity element).
    """
    results = []
    for decay in decay_fracs:
        # Generate N pair-vectors
        A = [hdc.klein4_random(D, rng) for _ in range(N)]
        B = [hdc.klein4_random(D, rng) for _ in range(N)]
        bound = [hdc.klein4_bind(a, b) for a, b in zip(A, B)]
        # Apply decay to each bound pair
        n_decay = int(decay * D)
        if n_decay > 0:
            for vec in bound:
                positions = rng.choice(D, size=n_decay, replace=False)
                vec[positions] = 0  # klein-4 state 0 is identity
        composite = hdc.klein4_bundle(*bound)
        # Query
        sims = [float(hdc.klein4_similarity(hdc.klein4_unbind(composite, A[i]), B[i])) for i in range(N)]
        base = random_baseline_klein4(D, rng)
        above_rand = (float(np.mean(sims)) - base) / (1 - base)
        results.append({"decay": decay, "sim": float(np.mean(sims)), "above_rand": above_rand})
    return results


# === Item 19: Decay-recovery dynamics (Hebbian rehearsal) ===
def item_19_decay_recovery(D, N, rng):
    """Simulate Hebbian rehearsal: bind -> decay -> rebind (rehearsal) -> bundle -> query."""
    A = [hdc.polar_random(D, rng) for _ in range(N)]
    B = [hdc.polar_random(D, rng) for _ in range(N)]

    # Initial bind
    bound = [hdc.polar_bind(a, b) for a, b in zip(A, B)]

    # Apply 50% decay
    decay_frac = 0.5
    n_decay = int(decay_frac * D)
    decayed = []
    for vec in bound:
        v = vec.copy()
        positions = rng.choice(D, size=n_decay, replace=False)
        v[positions] = 0
        decayed.append(v)

    # Stage 1 retrieval (after decay)
    composite_decayed = hdc.polar_bundle(*decayed)
    base = random_baseline_polar(D, rng)
    sims_decayed = [float(hdc.polar_similarity(hdc.polar_unbind(composite_decayed, A[i]), B[i])) for i in range(N)]
    above_decayed = (float(np.mean(sims_decayed)) - base) / (1 - base)

    # Rehearsal: re-apply 50% of the original bind information
    rehearsed = []
    for orig, dec in zip(bound, decayed):
        # Rehearsal restores some of the lost bindings:
        # at positions where dec=0 but orig was non-zero, restore orig with 50% probability
        v = dec.copy()
        zero_pos = np.where(dec == 0)[0]
        rehearse_count = int(0.5 * len(zero_pos))
        if rehearse_count > 0:
            to_rehearse = rng.choice(zero_pos, size=rehearse_count, replace=False)
            v[to_rehearse] = orig[to_rehearse]
        rehearsed.append(v)

    composite_rehearsed = hdc.polar_bundle(*rehearsed)
    sims_rehearsed = [float(hdc.polar_similarity(hdc.polar_unbind(composite_rehearsed, A[i]), B[i])) for i in range(N)]
    above_rehearsed = (float(np.mean(sims_rehearsed)) - base) / (1 - base)

    return {
        "after_decay": {"sim": float(np.mean(sims_decayed)), "above_rand": above_decayed},
        "after_rehearsal_50%": {"sim": float(np.mean(sims_rehearsed)), "above_rand": above_rehearsed},
        "signal_recovery_pct": float((above_rehearsed - above_decayed) / above_decayed * 100) if above_decayed > 0 else None,
    }


# === Item 21: Noise vs decay distinction ===
def item_21_noise_vs_decay(D, N, rng):
    """Compare bit-flip noise vs zero-injection decay at matched fractions."""
    fraction = 0.3
    n_corrupt = int(fraction * D)
    A = [hdc.polar_random(D, rng) for _ in range(N)]
    B = [hdc.polar_random(D, rng) for _ in range(N)]
    bound = [hdc.polar_bind(a, b) for a, b in zip(A, B)]

    # Noise: flip sign of non-zero positions
    noise_bound = []
    for vec in bound:
        v = vec.copy()
        positions = rng.choice(D, size=n_corrupt, replace=False)
        nz_at_pos = positions[v[positions] != 0]
        v[nz_at_pos] = -v[nz_at_pos]
        noise_bound.append(v)

    # Decay: zero out positions
    decay_bound = []
    for vec in bound:
        v = vec.copy()
        positions = rng.choice(D, size=n_corrupt, replace=False)
        v[positions] = 0
        decay_bound.append(v)

    comp_noise = hdc.polar_bundle(*noise_bound)
    comp_decay = hdc.polar_bundle(*decay_bound)

    base = random_baseline_polar(D, rng)
    sims_noise = [float(hdc.polar_similarity(hdc.polar_unbind(comp_noise, A[i]), B[i])) for i in range(N)]
    sims_decay = [float(hdc.polar_similarity(hdc.polar_unbind(comp_decay, A[i]), B[i])) for i in range(N)]

    return {
        "noise_above_rand": (float(np.mean(sims_noise)) - base) / (1 - base),
        "decay_above_rand": (float(np.mean(sims_decay)) - base) / (1 - base),
        "noise_density": float(hdc.polar_density(comp_noise)),
        "decay_density": float(hdc.polar_density(comp_decay)),
    }


# === Items 12, 20: Pareto frontiers ===
def items_12_20_pareto(rng):
    """Sweep (D, N) and (D, N, decay) for klein-4 chirality discrimination."""
    out = {"d_n_pareto": {}, "d_n_decay_pareto": {}}

    # D vs N Pareto for klein-4 (item 12)
    for D in [2048, 8192, 32768]:
        base = random_baseline_klein4(D, rng)
        for N in [8, 32, 128]:
            A = [hdc.klein4_random(D, rng) for _ in range(N)]
            B = [hdc.klein4_random(D, rng) for _ in range(N)]
            sectors = [i % 4 for i in range(N)]
            tagged_A = [hdc.klein4_bind(a, np.full(D, s, dtype=np.uint8)) for a, s in zip(A, sectors)]
            bound = [hdc.klein4_bind(a, b) for a, b in zip(tagged_A, B)]
            comp = hdc.klein4_bundle(*bound)
            sims = []
            for i in range(N):
                sims.append(float(hdc.klein4_similarity(
                    hdc.klein4_unbind(comp, tagged_A[i]), B[i]
                )))
            above_rand = (float(np.mean(sims)) - base) / (1 - base)
            out["d_n_pareto"][f"D{D}_N{N}"] = above_rand

    # D x N x decay (item 20) at klein-4
    for D in [4096, 16384]:
        base = random_baseline_klein4(D, rng)
        for N in [16, 64]:
            for decay in [0.0, 0.3]:
                A = [hdc.klein4_random(D, rng) for _ in range(N)]
                B = [hdc.klein4_random(D, rng) for _ in range(N)]
                bound = [hdc.klein4_bind(a, b) for a, b in zip(A, B)]
                # Apply decay
                if decay > 0:
                    for vec in bound:
                        positions = rng.choice(D, size=int(decay * D), replace=False)
                        vec[positions] = 0
                comp = hdc.klein4_bundle(*bound)
                sims = [float(hdc.klein4_similarity(hdc.klein4_unbind(comp, A[i]), B[i])) for i in range(N)]
                above_rand = (float(np.mean(sims)) - base) / (1 - base)
                out["d_n_decay_pareto"][f"D{D}_N{N}_decay{decay}"] = above_rand
    return out


# === Item 24: Polar + Klein-4 hybrid extended ===
def item_24_hybrid_extended(D, N, rng):
    """Test the hybrid encoder approach more thoroughly.

    Hybrid: klein-4 chirality tag + polar plasticity overlay.
    Bind two hybrid-encoded vectors; recover via polar unbind.
    """
    # Generate concept pairs as hybrid encodings (klein-4 sector tag + polar overlay)
    A_concepts = []
    B_concepts = []
    sectors = [i % 4 for i in range(N)]

    for i in range(N):
        # Stage 1: klein-4 with sector
        k4_a = hdc.klein4_random(D, np.random.default_rng(i * 31))
        k4_a_tagged = hdc.klein4_bind(k4_a, np.full(D, sectors[i], dtype=np.uint8))
        # Stage 2: convert to polar via state-pair XOR sign extraction
        polar_a = np.where(((k4_a_tagged >> 1) ^ (k4_a_tagged & 1)) == 0, 1, -1).astype(np.int8)
        # Apply density adjustment (50% non-zero)
        n_zero = int(0.5 * D)
        zero_pos = rng.choice(D, size=n_zero, replace=False)
        polar_a[zero_pos] = 0
        A_concepts.append(polar_a)

        k4_b = hdc.klein4_random(D, np.random.default_rng(i * 31 + 1))
        polar_b = np.where(k4_b > 1, 1, -1).astype(np.int8)
        polar_b[zero_pos] = 0
        B_concepts.append(polar_b)

    bound = [hdc.polar_bind(a, b) for a, b in zip(A_concepts, B_concepts)]
    comp = hdc.polar_bundle(*bound)
    base = random_baseline_polar(D, rng)
    sims = [float(hdc.polar_similarity(hdc.polar_unbind(comp, A_concepts[i]), B_concepts[i])) for i in range(N)]
    above_rand = (float(np.mean(sims)) - base) / (1 - base)
    return {
        "hybrid_sim": float(np.mean(sims)),
        "above_rand": above_rand,
        "composite_density": float(hdc.polar_density(comp)),
    }


# === Item 27: 4-way at signal level ===
def item_27_4way_signal_level(D, rng):
    """Simulate 4 chirality-distinct synthetic signals; encode each in one Klein-4 sector;
    verify retrieval discriminates by sector."""
    N = 16
    # 4 signal "types", 4 instances each
    signals = []
    sectors = []
    for sig_type in range(4):
        for instance in range(4):
            # Each signal type has its own chirality "shape" via a seed
            sig = np.random.default_rng(sig_type * 1000 + instance * 7).standard_normal(D)
            # Quantise to klein-4: state from (sign, magnitude > median)
            sign_bit = (sig > 0).astype(np.uint8)
            mag_bit = (np.abs(sig) > 0.5).astype(np.uint8)
            states = (sign_bit << 1) | mag_bit
            tagged = hdc.klein4_bind(states.astype(np.uint8), np.full(D, sig_type, dtype=np.uint8))
            signals.append(tagged)
            sectors.append(sig_type)
    composite = hdc.klein4_bundle(*signals)
    base = random_baseline_klein4(D, rng)

    # For each of the 4 sector queries, retrieve and check sector match precision
    sector_retrieval = {}
    for query_sector in range(4):
        unbound = hdc.klein4_unbind(composite, np.full(D, query_sector, dtype=np.uint8))
        # Score against all encoded signals
        sims = [float(hdc.klein4_similarity(unbound, sig)) for sig in signals]
        # Top-4 by sim
        top_4 = np.argsort(sims)[::-1][:4]
        correct = sum(1 for idx in top_4 if sectors[idx] == query_sector)
        sector_retrieval[query_sector] = {"top_4_correct": correct, "precision": correct / 4}
    return sector_retrieval


def main():
    rng = np.random.default_rng(42)
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print()

    D = 10000
    N = 16

    print("=== Item 18: Klein-4 under decay ===")
    decay_fracs = [0.0, 0.1, 0.3, 0.5, 0.7]
    r18 = item_18_klein4_decay(D, N, decay_fracs, rng)
    print(f"{'decay':>6} | {'sim':>10} | {'above-rand':>12}")
    for r in r18:
        print(f"{r['decay']:>6.2f} | {r['sim']:>+0.4f}    | {r['above_rand']:>+0.4f}")
    print()

    print("=== Item 19: Decay-recovery (Hebbian rehearsal) ===")
    r19 = item_19_decay_recovery(D, N, rng)
    print(f"  After 50% decay:        above-rand {r19['after_decay']['above_rand']:+0.4f}")
    print(f"  After 50% rehearsal:    above-rand {r19['after_rehearsal_50%']['above_rand']:+0.4f}")
    if r19['signal_recovery_pct'] is not None:
        print(f"  Signal recovery:        +{r19['signal_recovery_pct']:.1f}%")
    print()

    print("=== Item 21: Noise vs decay at matched fraction (0.3) ===")
    r21 = item_21_noise_vs_decay(D, N, rng)
    print(f"  Sign-flip noise (30%): above-rand {r21['noise_above_rand']:+0.4f}, density {r21['noise_density']:.4f}")
    print(f"  Zero-decay     (30%): above-rand {r21['decay_above_rand']:+0.4f}, density {r21['decay_density']:.4f}")
    print(f"  Decay-vs-noise advantage: {r21['decay_above_rand'] - r21['noise_above_rand']:+0.4f}")
    print()

    print("=== Items 12+20: Pareto frontiers ===")
    r1220 = items_12_20_pareto(rng)
    print("  D vs N Pareto (above-rand at each (D, N)):")
    for k, v in r1220["d_n_pareto"].items():
        print(f"    {k}: {v:+0.4f}")
    print("  D x N x decay Pareto:")
    for k, v in r1220["d_n_decay_pareto"].items():
        print(f"    {k}: {v:+0.4f}")
    print()

    print("=== Item 24: Polar + Klein-4 hybrid extended ===")
    r24 = item_24_hybrid_extended(D, N, rng)
    print(f"  Hybrid bind/bundle: sim={r24['hybrid_sim']:.4f}, above-rand {r24['above_rand']:+0.4f}, density {r24['composite_density']:.4f}")
    print()

    print("=== Item 27: 4-way at signal level (4 sectors, 4 signals each) ===")
    r27 = item_27_4way_signal_level(16384, rng)
    for sector, info in r27.items():
        print(f"  Sector {sector}: top-4 precision = {info['precision']:.2f} ({info['top_4_correct']}/4)")
    print()

    out = {
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D, "N": N,
        "item_18_klein4_decay": r18,
        "item_19_decay_recovery": r19,
        "item_21_noise_vs_decay": r21,
        "items_12_20_pareto": r1220,
        "item_24_hybrid": r24,
        "item_27_4way_signal": {str(k): v for k, v in r27.items()},
    }
    out_path = Path(__file__).parent / "R-RBS-LM-105_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()
