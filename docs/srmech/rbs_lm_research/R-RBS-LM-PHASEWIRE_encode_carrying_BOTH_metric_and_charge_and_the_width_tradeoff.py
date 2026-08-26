r"""R-RBS-LM-PHASEWIRE — wire the CURVATURE (charge) channel into the encode alongside the METRIC channel, and
characterise the cost. The deliverable is `encode_coupled(word, D)`: one Class-M carrier holding BOTH.

User (2026-07-20): *"wire the phase channel into the encode"* — following F1261, which measured that curvature
reaches a Class-M carrier through the POSITIONAL phase channel (not the sector alphabet: Klein-4 is Z2xZ2,
`bind(a,a)=identity`, so there is no order-4 sector cycle).

THE CONTRACT (F1228/F1246, now at the word layer):
  metric  = `klein4_encode_bytes(word, D)`  — byte-composed; morphology survives (F1260: cat/cats 0.6597)
  charge  = the word's glyph-graph HOLONOMY (F1255's exact integer fundamental-cycle residual)
  coupled = phase_bind(metric, |h| -> frac)          # MAGNITUDE ONLY -- see the sign caveat below

Cascade-honest decomposition of the charge, per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:
  * MAGNITUDE |h| is Class-K (pin-slot) -> the phase POSITION (a positional window, resolution ~D)  [WIRED]
  * SIGN(h)   is Class-C (chirality)    -> WHICH V4 axis (gamma5 / i-omega7)                        [NOT WIRED]
The sign design FAILED its own falsifier: the holonomy residual's sign is LABEL-ORDER DEPENDENT (nodes are
numbered by first appearance, so a word and its reverse canonicalise differently). Measured: stressed/desserts,
aardvark/kravdraa, abcabc/cbacba ALL return the SAME sign -- no flip on reversal. Same defect class as srmech
#1440. The falsifier now runs as a standing check in this harness; see `encode_coupled` for the fix sketch.

THE RISK THIS MEASURES, and it is the whole point: phase_bind OVERWRITES a `width`-wide window of the carrier.
The default width is D//2 -- half the vector -- which would badly damage the morphology F1260 just restored.
So this sweeps width and reports the TRADEOFF instead of asserting a setting:
  A. MORPHOLOGY RETENTION  — same-holonomy related pairs must stay close to the metric-only baseline
  B. CURVATURE SEPARABILITY — different-holonomy words must become distinguishable
  C. THE FRONTIER          — the width where both hold; if none exists, the wiring is a REGRESSION and we say so.

srmech 0.9.0rc288. No numpy. Integers for the holonomy; float only at the frac boundary (a display/API edge).
Composes F1261 (the phase channel measured), F1255 (exact holonomy), F1260 (the metric channel),
F1211 (abelian bind = why not the sector channel), F130/F132 (the bi-axial chirality pair), F861/§59.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-PHASEWIRE_*.py
"""
import importlib.util as iu
import sys
import time
from pathlib import Path

from srmech.amsc import cascade, hdc

HERE = Path(__file__).resolve().parent
D = 8192
MOD = 16                      # holonomy wraps into the phase circle at this modulus
GAMMA5, OMEGA7 = 2, 1         # the two V4 chirality axes (F130): + holonomy -> gamma5, - -> i-omega7
T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def _gauge():
    p = next(HERE.glob("R-RBS-LM-GAUGE_*.py"))
    spec = iu.spec_from_file_location("g", p)
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _gauge()


# ---------------------------------------------------------------- the charge read
def holonomy_signed(word):
    """The word's glyph-graph holonomy as a SIGNED integer (F1255). 0 == gauge-trivial (acyclic or exact)."""
    order, edges, charges = G.glyph_graph(word)
    if not edges:
        return 0
    n = len(order)
    adj = {i: [] for i in range(n)}
    for k, (u, v) in enumerate(edges):
        adj[u].append((v, k, +1))
        adj[v].append((u, k, -1))
    from collections import deque
    phi, tree, comps = {}, set(), 0
    for s in range(n):
        if s in phi:
            continue
        comps += 1
        phi[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v, k, sgn in adj[u]:
                if v not in phi:
                    phi[v] = phi[u] + sgn * charges[k]
                    tree.add(k)
                    q.append(v)
    for k, (u, v) in enumerate(edges):
        if k in tree:
            continue
        r = charges[k] - (phi[v] - phi[u])
        if r != 0:
            return r                      # SIGNED — the sign is the Class-C which-way
    return 0


# ---------------------------------------------------------------- THE ENCODER
def encode_coupled(word, dim=D, *, mod=MOD, width=None):
    """ONE Class-M carrier holding the metric channel PLUS the curvature MAGNITUDE.

    metric : byte-composed (morphology)          — F1260
    charge : |holonomy| -> positional phase      — F1261; Class-K pin-slot magnitude
    A gauge-trivial word (h == 0) is returned UNTRANSPORTED — there is no curvature to record.

    ⚠️ THE SIGN CHANNEL IS NOT WIRED, and deliberately so (measured 2026-07-20).
    The intended design was: sign(h) (Class-C) -> which V4 chirality axis (γ₅ vs iω₇), giving the
    F130 bi-axial pair a real job. It does not work as posed, because **the sign of the holonomy
    residual is LABEL-ORDER DEPENDENT**, not a chirality signal:

        stressed  nodes ['s','t','r','e','d']  charges [1, 0, 1,  1, 1]
        desserts  nodes ['d','e','s','r','t']  charges [1, 0, 1, -1, 1]

    Nodes are numbered by FIRST APPEARANCE, so the canonical (i<j) edge orientation differs between
    a word and its reverse, and `holonomy_signed` (which returns the first nonzero non-tree residual)
    picks a sign determined by that arbitrary numbering. Measured: `stressed`/`desserts`,
    `aardvark`/`kravdraa` and `abcabc`/`cbacba` ALL return the SAME sign — no flip on reversal.

    This is structurally the SAME defect class as srmech #1440 (`mat_eigvals` was label-order
    dependent, which is why path/cycle spot-checks passed). Feeding that sign to the axis choice
    would have shipped an arbitrary chirality label that looked principled.

    To wire the sign channel properly the cycle needs a CANONICAL ORIENTATION independent of node
    numbering — e.g. orienting each fundamental cycle by first-appearance POSITION IN THE STRING
    rather than by node index — and the falsifier is exactly the one above: reversal must flip it.
    Until that exists, `elem` stays fixed at γ₅ and the encode carries MAGNITUDE ONLY.
    """
    metric = hdc.klein4_encode_bytes(word, dim)
    h = holonomy_signed(word)
    if h == 0:
        return metric
    mag = cascade.magnitude(h)                       # Class-K pin-slot, never the builtin
    return hdc.klein4_phase_bind(metric, (mag % mod) / mod, elem=GAMMA5, width=width)


def sim(a, b):
    return hdc.klein4_similarity(a, b)


# ---------------------------------------------------------------- characterisation
MORPH_PAIRS = [("cat", "cats"), ("walk", "walked"), ("nation", "national"),
               ("run", "running"), ("the", "then"), ("place", "places")]
UNREL_PAIRS = [("cat", "dog"), ("nation", "running"), ("the", "place")]


def main():
    import srmech
    log("=== PHASEWIRE (srmech %s) — encode carrying BOTH metric and charge ===" % srmech.__version__)

    log("")
    log("--- the charge read on the probe vocabulary (signed holonomy, F1255) ---")
    voc = sorted({w for p in MORPH_PAIRS + UNREL_PAIRS for w in p} |
                 {"stressed", "desserts", "aardvark", "banana", "mississippi", "level"})
    for w in voc:
        h = holonomy_signed(w)
        log("   %-14s h = %-4d %s" % (w, h, "gauge-trivial (no transport)" if h == 0 else
                                      "CURVED -> %s axis" % ("gamma5" if h > 0 else "i-omega7")))

    # ---------- THE SIGN FALSIFIER (standing check: must flip on reversal) ----------
    log("")
    log("--- SIGN CHANNEL FALSIFIER — holonomy sign MUST flip under reversal to be chirality ---")
    any_flip = False
    for a, b in (("stressed", "desserts"), ("aardvark", "kravdraa"), ("abcabc", "cbacba")):
        ha, hb = holonomy_signed(a), holonomy_signed(b)
        flips = (ha == -hb and ha != 0)
        any_flip = any_flip or flips
        log("   %-10s h=%-4d  %-10s h=%-4d  -> %s" %
            (a, ha, b, hb, "FLIPS" if flips else "same sign — LABEL-ORDER ARTIFACT, not chirality"))
    log("   => sign channel %s" % ("WIRED" if any_flip else
                                   "NOT wired (magnitude only) — needs a canonical cycle orientation"))

    # ---------- the width sweep: does the charge channel cost us the metric channel? ----------
    log("")
    log("--- THE TRADEOFF: width sweep (default width = D//2 = %d) ---" % (D // 2))
    log("  %-9s %-14s %-14s %-14s %-10s" %
        ("width", "morph(coupled)", "morph(metric)", "retention", "unrel"))
    base_morph = sum(sim(hdc.klein4_encode_bytes(a, D), hdc.klein4_encode_bytes(b, D))
                     for a, b in MORPH_PAIRS) / len(MORPH_PAIRS)
    base_unrel = sum(sim(hdc.klein4_encode_bytes(a, D), hdc.klein4_encode_bytes(b, D))
                     for a, b in UNREL_PAIRS) / len(UNREL_PAIRS)
    rows = []
    for width in (D // 2, D // 4, D // 8, D // 16, D // 32, D // 64, D // 128):
        m = sum(sim(encode_coupled(a, width=width), encode_coupled(b, width=width))
                for a, b in MORPH_PAIRS) / len(MORPH_PAIRS)
        u = sum(sim(encode_coupled(a, width=width), encode_coupled(b, width=width))
                for a, b in UNREL_PAIRS) / len(UNREL_PAIRS)
        ret = m / base_morph if base_morph else 0.0
        rows.append((width, m, u, ret))
        log("  %-9d %-14.4f %-14.4f %-14.3f %-10.4f" % (width, m, base_morph, ret, u))

    # ---------- can the coupled carrier still SEE curvature? ----------
    log("")
    log("--- CURVATURE SEPARABILITY at each width (same metric, different holonomy) ---")
    log("  synthetic control: one word's metric, transported by different holonomies")
    metric = hdc.klein4_encode_bytes("control", D)
    log("  %-9s %-22s %-22s" % ("width", "max off-diag sim", "verdict"))
    for width in (D // 2, D // 4, D // 8, D // 16, D // 32, D // 64, D // 128):
        vs = {}
        for h in (1, 2, 3, 5, 8):
            vs[h] = hdc.klein4_phase_bind(metric, (h % MOD) / MOD, elem=GAMMA5, width=width)
        mx = max(sim(vs[a], vs[b]) for a in vs for b in vs if a != b)
        log("  %-9d %-22.4f %-22s" % (width, mx, "separable" if mx < 0.95 else "NOT separable"))

    # ---------- the frontier ----------
    log("")
    log("--- THE FRONTIER: is there a width where BOTH channels survive? ---")
    good = []
    for width, m, u, ret in rows:
        vs = {h: hdc.klein4_phase_bind(metric, (h % MOD) / MOD, elem=GAMMA5, width=width)
              for h in (1, 2, 3, 5, 8)}
        mx = max(sim(vs[a], vs[b]) for a in vs for b in vs if a != b)
        if ret >= 0.90 and mx < 0.95:
            good.append((width, ret, mx))
    if good:
        log("  widths keeping morphology >=90%% of baseline AND curvature separable:")
        for width, ret, mx in good:
            log("     width=%-6d retention %.3f   max off-diag %.4f" % (width, ret, mx))
        log("")
        log("  RECOMMENDED: width = %d (the widest that holds both -> strongest phase signal)" % good[0][0])
    else:
        log("  *** NO WIDTH SATISFIES BOTH — wiring the phase channel in this form is a REGRESSION. ***")

    # ---------- the honest end-to-end read ----------
    log("")
    log("--- END-TO-END at the recommended width ---")
    W = good[0][0] if good else D // 32
    log("  %-22s %-12s %-12s" % ("pair", "metric-only", "coupled"))
    for a, b in MORPH_PAIRS + UNREL_PAIRS:
        mo = sim(hdc.klein4_encode_bytes(a, D), hdc.klein4_encode_bytes(b, D))
        co = sim(encode_coupled(a, width=W), encode_coupled(b, width=W))
        log("  %-22s %-12.4f %-12.4f" % ("%s/%s" % (a, b), mo, co))
    log("")
    log("  curvature-bearing pair that the METRIC alone cannot separate:")
    for a, b in (("stressed", "desserts"),):
        mo = sim(hdc.klein4_encode_bytes(a, D), hdc.klein4_encode_bytes(b, D))
        co = sim(encode_coupled(a, width=W), encode_coupled(b, width=W))
        log("  %-22s metric %.4f -> coupled %.4f  (h=%d vs h=%d)" %
            ("%s/%s" % (a, b), mo, co, holonomy_signed(a), holonomy_signed(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
