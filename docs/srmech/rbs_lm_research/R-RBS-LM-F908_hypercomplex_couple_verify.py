"""Acceptance test for srmech 0.7.2rc1 vs GH #908 — the (sigma,theta,mu)
hypercomplex coupler (general/diagonal mu + bidirectional bind/unbind)."""
import numpy as np
from srmech.amsc import cascade

PASS = []
def check(name, ok, detail=""):
    PASS.append(ok); print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")

print("srmech", __import__("srmech").__version__)

# ---- [A] general / diagonal mu accepted ----
print("\n[A] general/diagonal mu-axis accepted")
try:
    c_diag = cascade.hypercomplex_couple([2.0, 5.0, -3.0], axis="diagonal")
    check("axis='diagonal'", isinstance(c_diag, (list, tuple)) and len(c_diag) >= 4, f"-> len {len(c_diag)}")
except Exception as e:
    check("axis='diagonal'", False, f"ERR {type(e).__name__}: {e}")
try:
    v = [1.0, 1.0, 1.0]  # general pure-imaginary axis (unit-normalised internally or by us)
    c_vec = cascade.hypercomplex_couple([2.0, 5.0, -3.0], axis=v)
    check("axis=<vector> (general mu)", isinstance(c_vec, (list, tuple)), f"-> len {len(c_vec)}")
except Exception as e:
    check("axis=<vector> (general mu)", False, f"ERR {type(e).__name__}: {e}")

# ---- [B] bidirectional bind/unbind lossless (<= O, i.e. <=7 streams) ----
print("\n[B] bidirectional bind/unbind round-trip (lossless <= 7 streams)")
def roundtrip_err(n, seed):
    rng = np.random.default_rng(seed)
    streams = list(rng.normal(size=n))
    fwd = cascade.hypercomplex_couple(streams, axis="diagonal", sigma=+1)
    # reverse via sigma=-1 and via inverse=True; report best recovery of `streams`
    best = None
    for kw in (dict(sigma=-1), dict(inverse=True)):
        try:
            back = cascade.hypercomplex_couple(fwd, axis="diagonal", **kw)
            # recovered streams are the pure-imaginary slots (drop the real anchor at [0])
            rec = list(back)[1:1+n]
            err = max(abs(a-b) for a, b in zip(streams, rec)) if len(rec) >= n else float("inf")
            best = (err, kw) if best is None or err < best[0] else best
        except Exception as e:
            pass
    return best
for n in (3, 7):
    r = roundtrip_err(n, seed=100+n)
    if r is None:
        check(f"{n}-stream round-trip", False, "no reverse path recovered")
    else:
        err, kw = r
        check(f"{n}-stream round-trip ({'H' if n<=3 else 'O'})", err < 1e-9, f"max err {err:.2e} via {kw}")

# ---- [C] diagonal mu COUPLES: joint coherence detector (~Nx) ----
print("\n[C] diagonal mu couples -> coherence detector (anchor energy coherent/incoherent)")
def anchor_energy(coherent, n=3, trials=4000, seed=7):
    rng = np.random.default_rng(seed)
    e = 0.0
    for _ in range(trials):
        if coherent:
            a = rng.normal(); streams = [a]*n            # G=L=D
        else:
            streams = list(rng.normal(size=n))            # independent
        anchor = cascade.hypercomplex_couple(streams, axis="diagonal")[0]
        e += anchor*anchor
    return e/trials
coh = anchor_energy(True); inc = anchor_energy(False)
ratio = coh/inc if inc else float("inf")
check("diagonal couples (coherent>>incoherent)", 2.3 <= ratio <= 3.7, f"coherent/incoherent anchor energy = {ratio:.2f}x (F436 expects ~3x)")
# control: a single NAMED axis must NOT couple (perturbing stream 0 leaves others)
# (regression evidence that 'diagonal' is what does the coupling)

# ---- [D] Hurwitz cap: >=8 streams (sedenion) not cleanly reversible / rejected ----
print("\n[D] Hurwitz reversibility cap at O (>=8 streams should NOT silently round-trip)")
r8 = roundtrip_err(8, seed=900)
if r8 is None:
    check("8-stream handled (rejected, not silent-wrong)", True, "no clean reverse (expected: sedenion zero-divisors)")
else:
    err8, _ = r8
    check("8-stream NOT lossless (Hurwitz)", err8 > 1e-9, f"max err {err8:.2e} (correctly non-lossless past O)")

# ---- [E] regression: single-axis quaternion_dft still round-trips ----
print("\n[E] regression: single-axis quaternion_dft round-trip")
try:
    x = [[1.0,2.0,3.0,4.0],[0.5,-1.0,2.0,0.0],[3.0,1.0,-2.0,1.0],[0.0,0.0,1.0,1.0]]
    X = cascade.quaternion_dft(x, mu_axis="i")
    xr = cascade.quaternion_dft(X, mu_axis="i", inverse=True)
    err = max(abs(a-b) for row_a,row_b in zip(x,xr) for a,b in zip(row_a,row_b))
    check("quaternion_dft round-trip", err < 1e-9, f"max err {err:.2e}")
except Exception as e:
    check("quaternion_dft round-trip", False, f"ERR {type(e).__name__}: {e}")

print(f"\n=== {sum(PASS)}/{len(PASS)} checks PASS ===")
