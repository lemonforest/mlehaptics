"""F1181 (#243): the FRACTAL ADVANTAGE — do MULTI-SCALE (fractal, subharmonic-comb) copies reinforce better than
SAME-SCALE (single-period) copies, at equal redundancy?

Each value is stored at k copy-offsets from its position. FAIR comparison — same k, same total span, differing only in
the DISTRIBUTION of the copies:
  SAME-SCALE  = arithmetic spacing (all copies at one fundamental period P and its harmonics): P, 2P, ..., kP.
  MULTI-SCALE = geometric spacing (the fractal subharmonic comb, F1171): 1, 2, 4, 8, ..., 2^(k-1).
A value is recoverable if >=1 of its copy-positions is uncorrupted. Two corruption models:
  (A) i.i.d. scattered noise (each position independently) ;  (B) a contiguous BURST (a lacuna / scale-localized damage).
Prediction: EQUAL under i.i.d. (both k independent copies); MULTI-SCALE WINS under burst (a far-scale copy always
escapes a finite burst). numpy-free; no magnitude-builtin; plain arithmetic.
"""
import random

N = 8192
K = 7
SPAN = 2 ** (K - 1)                                  # 64
MULTI = [2 ** i for i in range(K)]                   # 1,2,4,8,16,32,64  (fractal / subharmonic comb)
P = SPAN // K or 1
SAME = [P * (i + 1) for i in range(K)]               # 9,18,27,...  (single fundamental scale + harmonics), same span

random.seed(7)


def recover_rate(offsets, corrupted):
    """of the corrupted primary positions, the fraction with >=1 uncorrupted copy (recoverable)."""
    rec = tot = 0
    for n in corrupted:
        tot += 1
        if any(((n + off) % N) not in corrupted for off in offsets):
            rec += 1
    return rec / max(1, tot)


print("F1181 (#243) fractal advantage: multi-scale (subharmonic comb) vs same-scale copies, k=%d, span=%d\n" % (K, SPAN))
print("   same-scale offsets  = %s" % SAME)
print("   multi-scale offsets = %s\n" % MULTI)

print("A. i.i.d. scattered noise (control — expect EQUAL):")
print("   corrupt%   same-scale   multi-scale   advantage")
for pct in (10, 20, 30, 40):
    corrupted = set(i for i in range(N) if random.random() < pct / 100)
    s = recover_rate(SAME, corrupted); m = recover_rate(MULTI, corrupted)
    print("     %2d       %.3f        %.3f       %+.3f" % (pct, s, m, m - s))

print("\nB. contiguous BURST (a lacuna / scale-localized damage — expect MULTI-SCALE to win):")
print("   burst-len   same-scale   multi-scale   advantage")
for L in (8, 16, 32, 48, 64, 96, 128):
    ss = ms = trials = 0
    for _ in range(40):
        b = random.randrange(N)
        corrupted = set((b + j) % N for j in range(L))
        ss += recover_rate(SAME, corrupted); ms += recover_rate(MULTI, corrupted); trials += 1
    s = ss / trials; m = ms / trials
    print("     %3d        %.3f        %.3f       %+.3f%s" % (L, s, m, m - s, "   <- fractal advantage" if m - s > 0.03 else ""))

print("\n  (Test B matched the SPANS, so both reach ~64 -> the advantage is distribution-only and SMALL. The real fractal")
print("  advantage is REACH, not within-span distribution:)")

print("\nC. FIXED fundamental scale (the honest framework comparison — same k copies, same cost, exponential reach):")
Pf = 4
SAME_F = [Pf * (i + 1) for i in range(K)]            # 4,8,12,...,28   reach = k*P  (LINEAR in k)
MULTI_F = [Pf * (2 ** i) for i in range(K)]          # 4,8,16,...,256  reach = 2^(k-1)*P  (EXPONENTIAL in k)
print("   same-scale offsets  = %s   (reach %d, linear in k)" % (SAME_F, SAME_F[-1]))
print("   multi-scale offsets = %s   (reach %d, exponential in k)\n" % (MULTI_F, MULTI_F[-1]))
print("   burst-len   same-scale   multi-scale   advantage")
for L in (16, 32, 64, 128, 200, 260, 400):
    ss = ms = trials = 0
    for _ in range(40):
        b = random.randrange(N)
        corrupted = set((b + j) % N for j in range(L))
        ss += recover_rate(SAME_F, corrupted); ms += recover_rate(MULTI_F, corrupted); trials += 1
    s = ss / trials; m = ms / trials
    print("     %3d        %.3f        %.3f       %+.3f%s" % (L, s, m, m - s, "   <- FRACTAL ADVANTAGE" if m - s > 0.05 else ""))

print("\n  READ: under scattered noise the two are equal (redundancy is redundancy). Under a BURST at a FIXED scale (Test C),")
print("  the multi-scale subharmonic comb reaches EXPONENTIALLY further for the SAME number of copies -> it survives bursts")
print("  far larger than single-scale redundancy does. Real damage (lacunae, torn corners, a transient at one band) is")
print("  BURSTY, so the fractal comb is why biology/antiquity store across scales, not at one: log-many copies cover")
print("  exponentially-many scales. 'Harmonic' (multi-scale) reinforcement genuinely beats merely 'redundant'.")
