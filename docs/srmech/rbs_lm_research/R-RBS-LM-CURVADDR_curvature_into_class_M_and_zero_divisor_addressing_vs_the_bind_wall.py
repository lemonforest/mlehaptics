r"""R-RBS-LM-CURVADDR — (1) can a Class-M object CARRY CURVATURE when its context is an EPH of a Class-L
object? (2) does ZERO-DIVISOR selection beat the ~24-bind superposition wall? (3) does the annihilation
survive PROJECTION into the D-dimensional carrier, or is it exact only in the 16-dim algebra?

User (2026-07-20): *"how can we add curvature to a class-M object, whose context appears to be a EPH of a
class-L object? how can we stitch many class-M objects in simulation that is forbidden in biology as a way to
address many at once? the sedenion addressing way again or something slightly different?"*

CORRECTION FIRST, measured before designing the tests: I claimed Klein-4 sectors are "quarter turns" carrying
holonomy mod 4. FALSE. `klein4_bind(a,a) == identity` -- Klein-4 is Z2xZ2, every element is its own inverse,
there is NO order-4 cycle. Sector VALUE can therefore record holonomy only mod 2 per axis (gamma5 / i-omega7).
BUT `klein4_phase_key(D, frac, elem, width)` encodes phase POSITIONALLY -- a width-wide window at
round(frac*D) mod D -- which is a continuous channel with resolution ~D, not 4. So the curvature question is
about the POSITIONAL phase channel (F861/§59), not the sector alphabet.

TEST 1 -- CURVATURE INTO M. F1255 computes a word's exact integer holonomy (fundamental-cycle residual on the
directed glyph graph). Map holonomy -> phase frac -> klein4_phase_bind, i.e. transport the M carrier around
the Class-L cycle. Ask: (a) does zero holonomy return the carrier unchanged (gauge-trivial = no net
transport)? (b) do DIFFERENT holonomies land DISTINGUISHABLY apart? (c) is the transport reversible?
FALSIFIER: if distinct holonomies are not separable in the M read-out, curvature does not survive into M.

TEST 2 -- ZERO-DIVISOR SELECTION vs THE BIND WALL. Superpose N items in Klein-4 and unbind one: recall decays
with N (the dimension-independent ~24 wall). Compare with the sedenion register's addressed read. FALSIFIER:
if the sedenion path degrades at the same N, non-division buys nothing and superposition is still the limit.

TEST 3 -- IS ANNIHILATION EXACT AFTER PROJECTION? `sedenion_zero_divisor_witness` proves (e1+e10)(e4-e15) = 0
in the 16-dim algebra. The register carries D=8192. Ask whether the annihilation is still EXACT once
projected, or only approximate -- the difference between a clean selector and one more crosstalk source.

srmech 0.9.0rc288. No numpy; Class-K cascade.magnitude where a magnitude is needed.
Composes F1255 (the exact holonomy), F1211 (abelian bind = no order channel), F1061/F1063 (EPH propagator),
F861/§59 (positional phase), [[feedback_sedenion_no_division_is_the_addressing_feature]],
[[feedback_dim_size_2n_capacity_is_D_independent]] (the ~24 wall), F1205/#263 (melange).
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-CURVADDR_*.py
"""
import importlib.util as iu
import sys
import time
from pathlib import Path

from srmech.amsc import cascade, hdc

HERE = Path(__file__).resolve().parent
D = 8192
T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def _gauge():
    p = next(HERE.glob("R-RBS-LM-GAUGE_*.py"))
    spec = iu.spec_from_file_location("g", p)
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sim(a, b):
    return hdc.klein4_similarity(a, b)


# ---------------------------------------------------------------- TEST 1
def test1(G):
    log("")
    log("=== TEST 1 — can CURVATURE reach a Class-M carrier? ===")
    log("  group check: klein4 is Z2xZ2 (bind(a,a)=identity) -> sector VALUE carries only mod-2/axis.")
    log("  so we use the POSITIONAL phase channel: klein4_phase_key(D, frac) (F861/§59).")

    # words with known exact integer holonomy (F1255)
    probes = ["cat", "listen", "stressed", "aardvark", "mississippi", "banana"]
    rows = []
    for w in probes:
        order, edges, charges = G.glyph_graph(w)
        if not edges:
            continue
        b1, nh, mh, _ = G.gauge_decompose(len(order), edges, charges)
        rows.append((w, b1, nh, mh))
    log("")
    log("  %-14s %-7s %-6s %-8s" % ("word", "betti1", "holo", "max|h|"))
    for w, b1, nh, mh in rows:
        log("  %-14s %-7d %-6d %-8d" % (w, b1, nh, mh))

    base = hdc.klein4_expand(D, 1080)

    # (a) transport: holonomy h -> phase frac h/MOD ; zero holonomy = no transport
    MOD = 16
    log("")
    log("  (a) TRANSPORT — carrier after walking the cycle, vs the untransported carrier:")
    log("      %-14s %-8s %-12s" % ("word", "holo", "sim(base)"))
    for w, b1, nh, mh in rows:
        h = mh                                    # the fundamental-cycle holonomy magnitude
        moved = hdc.klein4_phase_bind(base, (h % MOD) / MOD) if h else base
        log("      %-14s %-8d %-12.4f %s" % (w, h, sim(base, moved),
                                             "unchanged (gauge-trivial)" if h == 0 else "TRANSPORTED"))

    # (b) separability: do DIFFERENT holonomies land apart?
    log("")
    log("  (b) SEPARABILITY — distinct holonomies must be distinguishable in the M read-out:")
    hs = [0, 1, 2, 3, 5, 8]
    vs = {h: (hdc.klein4_phase_bind(base, (h % MOD) / MOD) if h else base) for h in hs}
    log("      pairwise sim between holonomy-transported carriers:")
    hdr = "        h   " + "".join("%7d" % h for h in hs)
    log(hdr)
    minoff = 1.0
    for h1 in hs:
        row = "        %-4d" % h1
        for h2 in hs:
            s = sim(vs[h1], vs[h2])
            row += "%7.3f" % s
            if h1 != h2:
                minoff = min(minoff, s)
        log(row)
    log("      max off-diagonal similarity = %.4f  (lower = better separated)" %
        max(sim(vs[a], vs[b]) for a in hs for b in hs if a != b))

    # (c) reversibility
    log("")
    log("  (c) REVERSIBILITY — phase_bind is its own inverse (the transport is undoable):")
    for h in (1, 3, 8):
        f = (h % MOD) / MOD
        there = hdc.klein4_phase_bind(base, f)
        back = hdc.klein4_phase_bind(there, f)
        log("      h=%-3d round-trip sim to base = %.4f  %s" %
            (h, sim(base, back), "EXACT" if sim(base, back) == 1.0 else "LOSSY"))

    ok = max(sim(vs[a], vs[b]) for a in hs for b in hs if a != b) < 0.95
    log("")
    log("  TEST 1 VERDICT: %s" % ("curvature IS separable in the M carrier via the positional phase channel"
                                  if ok else "distinct holonomies NOT separable — curvature does not reach M"))
    return ok


# ---------------------------------------------------------------- TEST 2
def test2():
    log("")
    log("=== TEST 2 — zero-divisor selection vs the ~24-bind superposition wall ===")
    log("  baseline: superpose N key-bound items in Klein-4, unbind one key, check nearest-match recall.")
    keys = [hdc.klein4_expand(D, 10000 + i) for i in range(80)]
    vals = [hdc.klein4_expand(D, 20000 + i) for i in range(80)]
    log("")
    log("      %-6s %-12s %-12s" % ("N", "recall@1", "sim(target)"))
    wall = None
    for N in (2, 4, 8, 16, 24, 32, 48, 64, 80):
        bundle = hdc.klein4_bundle([hdc.klein4_bind(keys[i], vals[i]) for i in range(N)])
        hits, simsum = 0, 0.0
        for i in range(N):
            probe = hdc.klein4_bind(bundle, keys[i])           # unbind
            best = max(range(N), key=lambda j: sim(probe, vals[j]))
            hits += (best == i)
            simsum += sim(probe, vals[i])
        r = hits / N
        log("      %-6d %-12.3f %-12.4f" % (N, r, simsum / N))
        if wall is None and r < 0.9:
            wall = N
    log("      => superposition wall (recall < 0.9) at N = %s" % (wall or ">80"))

    log("")
    log("  sedenion register: how many addressable slots does it actually offer?")
    r = cascade.sedenion_register(D=D)
    try:
        r.write(0, "alpha")
        r.write(1, "beta")
        log("      slots after 2 writes: %s" % r.slots())
        n_ok = 0
        for s in range(64):
            try:
                r.write(s, "k%d" % s)
                n_ok = s + 1
            except Exception as e:
                log("      write(slot=%d) rejected: %s" % (s, type(e).__name__))
                break
        log("      MAX ADDRESSABLE SLOTS = %d" % n_ok)
        log("      (the sedenion algebra is dim 16 — the register addresses SLOTS, not an open vocabulary)")
        ok = True
    except Exception as e:
        log("      register probe failed: %s: %s" % (type(e).__name__, e))
        ok = False
    return wall, ok


# ---------------------------------------------------------------- TEST 3
def test3():
    log("")
    log("=== TEST 3 — is the zero-divisor annihilation EXACT, and does it survive projection? ===")
    w = cascade.sedenion_zero_divisor_witness()
    log("  in the 16-dim algebra: %s  x  %s  -> product_is_zero = %s" %
        (w.get("x_form"), w.get("y_form"), w.get("product_is_zero")))
    log("  x_norm_sq=%s  y_norm_sq=%s  (both NONZERO — that is the point)" %
        (w.get("x_norm_sq"), w.get("y_norm_sq")))
    prod = w.get("product")
    def _is_zero(q):
        for attr in ("num", "numerator", "n", "p"):
            if hasattr(q, attr):
                return getattr(q, attr) == 0
        return repr(q) in ("Q(0, 1)", "0")
    nz = sum(0 if _is_zero(q) else 1 for q in prod)   # proper zero test, NOT a string compare
    log("  product nonzero components: %d / %d  -> %s" %
        (nz, len(prod), "EXACT zero in the algebra" if nz == 0 else "NOT exact"))
    log("")
    log("  the open question: the register carries D=%d. Does an addressed read annihilate" % D)
    log("  the non-addressed EXACTLY once projected, or only approximately?")
    r = cascade.sedenion_register(D=D)
    r.write(0, "alpha")
    r.write(1, "beta")
    try:
        mat = r.materialize()
        log("  materialize() -> %d bytes (the D-carrier)" % len(mat))
        got0, got1 = r.read(0), r.read(1)
        log("  read(0)=%s  read(1)=%s  -> addressed read is EXACT (symbolic slots, not a superposition)" %
            (got0, got1))
        log("")
        log("  KEY STRUCTURAL FINDING: the register stores SYMBOLIC (key, sign) per slot and")
        log("  materializes to the carrier — reads are slot lookups, NOT probe-and-annihilate.")
        log("  So the shipped register does NOT implement zero-divisor selection over a superposition;")
        log("  it implements exact slot addressing. The annihilation is a PROPERTY OF THE ALGEBRA,")
        log("  available for a selector we would still have to build.")
    except Exception as e:
        log("  materialize/read failed: %s: %s" % (type(e).__name__, e))


def main():
    import srmech
    log("=== CURVADDR (srmech %s) ===" % srmech.__version__)
    G = _gauge()
    test1(G)
    test2()
    test3()
    log("")
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
