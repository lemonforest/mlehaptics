"""Provenance script for `nucleosome_turn_asymmetry_frame_spike.md` (2026-07-19).

Every load-bearing number in that note is produced here
(`[[feedback_computational_provenance_discipline]]`). Exact integer / Class-N
rational arithmetic throughout; sign handled as a named Class-K pin-slot +
Class-C reorient composition, never `abs()`
(`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`). Floats appear
only in human-readable rendering.

Run:  python docs/srmech/notes/nucleosome_turn_asymmetry_frame_spike.py
Deps: srmech only (asymptotic_calculus / amsc.rational). No numpy, no math,
      no fractions (ADR-0005).

Blocks: C1 beat exact | C2 beat sensitivity | C3 structure-blind null
        C4 Wr + reciprocal frame | C5 discrimination null | C6 frame ledgers
        C7 structure-aware contacts | C8 numerology-hazard clearance
"""
"""Nucleosome turn/frame spike -- exact integer + Class-N rational arithmetic.

No float math for the load-bearing results; no abs() (Class-K pin-slot + Class-C
reorient composition instead). Floats appear ONLY in the final human-readable
rendering line of each block.
"""
import sys
sys.path.insert(0, r"D:\GitHub\mlehaptics\docs\srmech\python")
from srmech.amsc.rational import best_rational
from srmech import asymptotic_calculus as ac

# ---------------------------------------------------------------- primitives
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def rnorm(n, d):
    if d < 0:
        n, d = -n, -d
    g = gcd(n if n >= 0 else -n, d)
    return (n // g, d // g) if g else (n, d)

def radd(x, y):  return rnorm(x[0]*y[1] + y[0]*x[1], x[1]*y[1])
def rsub(x, y):  return rnorm(x[0]*y[1] - y[0]*x[1], x[1]*y[1])
def rmul(x, y):  return rnorm(x[0]*y[0], x[1]*y[1])
def rdiv(x, y):  return rnorm(x[0]*y[1], x[1]*y[0])
def rf(x):       return x[0] / x[1]

def class_k_pin(x):
    """Class-K pin-slot: split a rational into (chirality, magnitude).
    This is the project's sign-handling primitive -- NOT abs()."""
    n, d = x
    if n < 0:
        return (-1, (-n, d))
    if n > 0:
        return (+1, (n, d))
    return (0, (0, 1))

def class_c_reorient(sign, mag):
    """Class-C: re-apply a chirality to a magnitude."""
    return (sign * mag[0], mag[1])

def rcmp_mag(x, y):
    """Compare magnitudes without abs(): Class-K pin then integer cross-mul."""
    _, mx = class_k_pin(x)
    _, my = class_k_pin(y)
    return mx[0]*my[1] - my[0]*mx[1]

print("=" * 78)
print("C1 -- the two-periodicity BEAT, exact")
print("=" * 78)
N   = (147, 1)          # wrapped bp (Davey 2002 / McGinty&Tan: dyad on a bp -> odd)
h_s = (51, 5)           # 10.2 bp/turn, nucleosome surface   [Segura 2018]
h_0 = (21, 2)           # 10.5 bp/turn, free B-DNA solution  [Segura 2018]

beat_per_bp = rsub(rdiv((1,1), h_s), rdiv((1,1), h_0))
dPhi        = rmul(N, beat_per_bp)
print(f"  1/h_s - 1/h_0      = {beat_per_bp}  (turns per bp)")
print(f"  dPhi = N * beat    = {dPhi}  = {rf(dPhi):.6f} turns")
print(f"  Segura 2018 prints dPhi ~ +0.4          -> EXACT FORM 7/17")
print(f"  factorisation: 147 = 3*7^2 ; 1071 = 3^2*7*17 ; 441/1071 -> 7/17")

# exact commensuration at the FREE periodicity
turns_free = rdiv(N, h_0)
turns_surf = rdiv(N, h_s)
print(f"  N / h_0 = {turns_free} = {rf(turns_free)}   <- EXACT INTEGER 14")
print(f"  N / h_s = {turns_surf} = {rf(turns_surf):.6f}")
print(f"  detuning = {rsub(turns_surf, turns_free)} = {rf(rsub(turns_surf,turns_free)):.6f}")

print()
print("=" * 78)
print("C2 -- sensitivity of the beat to the periodicity inputs (the hazard)")
print("=" * 78)
hs_reports = [("Klug&Lutter 1981 (10.0)", (10,1)),
              ("Chandrasekhar 2024 (10.1)", (101,10)),
              ("Segura 2018 (10.2)", (51,5)),
              ("Bishop 2008 (10.4)", (52,5))]
h0_reports = [("Chandrasekhar 2024 (10.45)", (209,20)),
              ("Segura 2018 (10.5)", (21,2))]
print(f"  {'h_s':<28}{'h_0':<28}{'dPhi exact':>12}  {'float':>9}")
lo = hi = None
for ls, vs in hs_reports:
    for l0, v0 in h0_reports:
        d = rmul(N, rsub(rdiv((1,1), vs), rdiv((1,1), v0)))
        print(f"  {ls:<28}{l0:<28}{str(d):>12}  {rf(d):>9.4f}")
        if lo is None or rf(d) < rf(lo): lo = d
        if hi is None or rf(d) > rf(hi): hi = d
span = rsub(hi, lo)
print(f"  SPAN across attested inputs = {span} = {rf(span):.4f} turns")
print(f"  cf. attested dLk spread (-0.9..-1.5)  = 0.6 turns")
print(f"  -> the BEAT TERM's input-uncertainty is COMPARABLE TO the whole")
print(f"     physical spread of the quantity it is meant to explain.")

print()
print("=" * 78)
print("C3 -- Z/14 contact-lattice quantisation test (FALSIFIABLE PREDICTION)")
print("=" * 78)
# prediction: if the octamer contact lattice is Z/14 with one contact per DNA
# helical turn, sub/super-nucleosomal particles should wrap QUANTISED bp counts
# bp = spacing * (14 - k), k = contacts lost.
variants = [
    ("canonical NCP",        147, "PMC4378457 / Davey 2002"),
    ("601 NCP (stretched)",  145, "PMC4378457"),
    ("H2A.B nucleosome",     103, "PMC7780145"),
    ("H2A.Z.2.2 / H2A.B",    125, "PMC7780145"),
    ("H3-H4 octasome",       120, "PMC9659345"),
    ("hexasome",             115, "PMC6582347 (110-120 midpt)"),
    ("tetrasome",             70, "PMC9659345"),
    ("CENP-A (crystal)",     121, "PMC9010303"),
    ("CENP-A (native)",      133, "PMC5350519"),
    ("chromatosome +H1",     167, "PMC7801413"),
]
for label, spacing_n, spacing_d in [("spacing 10.5 bp (=h_0)", 21, 2),
                                    ("spacing 10.0 bp", 10, 1)]:
    print(f"\n  -- {label} --")
    print(f"  {'particle':<24}{'bp':>5}{'bp/s':>9}{'k_near':>8}{'resid(bp)':>11}")
    tot_n, tot_d = 0, 1
    cnt = 0
    for name, bp, _src in variants:
        q = rdiv((bp, 1), (spacing_n, spacing_d))            # bp / spacing
        k = (q[0] * 2 + q[1]) // (q[1] * 2)                   # nearest integer
        resid_turns = rsub(q, (k, 1))
        resid_bp = rmul(resid_turns, (spacing_n, spacing_d))
        sgn, mag = class_k_pin(resid_bp)                      # Class-K, not abs()
        tot_n, tot_d = radd((tot_n, tot_d), mag)
        cnt += 1
        print(f"  {name:<24}{bp:>5}{rf(q):>9.3f}{k:>8}{rf(resid_bp):>11.3f}")
    mean_resid = rdiv((tot_n, tot_d), (cnt, 1))
    null_mean = rdiv((spacing_n, spacing_d), (4, 1))   # uniform mod spacing
    print(f"  mean |resid| = {rf(mean_resid):.3f} bp   "
          f"vs uniform-random null = {rf(null_mean):.3f} bp")
    # Under the null, |resid| ~ Uniform[0, s/2]: mean s/4, var s^2/48.
    # Report z^2 EXACTLY (avoids a sqrt, keeps the test in integer/rational form):
    #   z^2 = n * diff^2 * 48 / s^2
    diff = rsub(mean_resid, null_mean)
    _, dmag = class_k_pin(diff)                        # Class-K, not abs()
    s2 = rmul((spacing_n, spacing_d), (spacing_n, spacing_d))
    z2 = rdiv(rmul(rmul((cnt, 1), rmul(dmag, dmag)), (48, 1)), s2)
    print(f"  z^2 = {z2} = {rf(z2):.4f}  -> |z| ~ {rf(z2) ** 0.5:.2f} sigma (n={cnt})")
    if rcmp_mag(mean_resid, null_mean) >= 0:
        verdict = "NO SIGNAL (worse than random)"
    elif rf(z2) >= 4:                                  # |z| >= 2
        verdict = "signal (|z| >= 2)"
    else:
        verdict = "NO SIGNAL (better than random but < 2 sigma -- not significant)"
    print(f"  VERDICT: {verdict}")

print()
print("=" * 78)
print("C4 -- Wr = n(1 - sin d): reproduce Segura, and the RECIPROCAL frame")
print("=" * 78)
# pi to enough digits via srmech Class-N cascade, as an exact rational
pi_s = ac.pi_cascade_digits(30)
pi_r = (int(pi_s.replace(".", "")), 10 ** (len(pi_s.split(".")[1])))
def deg2rad(dn, dd):
    return rdiv(rmul((dn, dd), pi_r), (180, 1))
for dn, dd, tag in [(3,1,"pitch 3 deg"), (4,1,"pitch 4 deg (Segura)"), (5,1,"pitch 5 deg")]:
    rad = deg2rad(dn, dd)
    s = ac.sin_series_truncate(rad[0], rad[1], 12)
    for n_turn, ntag in [((33,20),"n=1.65"), ((17,10),"n=1.70"),
                         ((6,5),"n=1.20 (H2A.B)"), ((19,10),"n=1.90 (chromatosome)")]:
        Wr = class_c_reorient(-1, rmul(n_turn, rsub((1,1), s)))
        if ntag in ("n=1.65", "n=1.90"):
            print(f"  {tag:<22}{ntag:<22}Wr = {rf(Wr):+.4f}"
                  + ("   <- Segura prints -1.53" if (dn,ntag)==(4,"n=1.65") else ""))
# reciprocal-frame: hold Wr, invert for n
rad4 = deg2rad(4, 1)
s4 = ac.sin_series_truncate(rad4[0], rad4[1], 12)
one_minus = rsub((1, 1), s4)
print(f"\n  RECIPROCAL FRAME (hold Wr, solve for n):  n = Wr / (1 - sin d)")
for Wr_n, Wr_d, tag in [(-146,100,"dWr=-1.46 (Segura measured-implied)"),
                        (-100,100,"dLk=-1.00 (classical, if dTw=0)"),
                        (-170,100,"dLk=-1.70 (Nikitina, if dTw=0)"),
                        (-126,100,"dLk=-1.26 (Segura measured)")]:
    n_back = rdiv((Wr_n, Wr_d), one_minus)
    sgn, mag = class_k_pin(n_back)
    # reduce to a uint64-safe pair before the Class-N anchor
    scaled = (mag[0] * 10**9 // mag[1], 10**9)
    print(f"    {tag:<40} n = {rf(mag):.4f} turns   "
          f"best_rational = {best_rational(scaled[0], scaled[1], 30)}")

print()
print("=" * 78)
print("C5 -- DISCRIMINATION TEST: does ~1.65 distinguish ANY candidate?")
print("=" * 78)
cands = [("phi  = (1+sqrt5)/2", (1618034, 1000000)),
         ("5/3", (5, 3)),
         ("147/89", (147, 89)),
         ("14/8.5 = 28/17", (28, 17)),
         ("sqrt(e) ~ 1.6487", (1648721, 1000000)),
         ("33/20 (=1.65 itself)", (33, 20)),
         ("17/10 (=1.70)", (17, 10))]
targ = (33, 20)
print(f"  {'candidate':<24}{'value':>10}{'|dev| from 1.65':>18}")
for nm, v in cands:
    dev = rsub(v, targ)
    _, mag = class_k_pin(dev)
    print(f"  {nm:<24}{rf(v):>10.5f}{rf(mag):>18.5f}")
print(f"\n  ATTESTED PHYSICAL SPREAD of the turn count (real, not scatter):")
print(f"    1.20 (H2A.B) .. 1.90 (chromatosome)   -> width 0.70 turns")
print(f"    canonical alone: 1.65 .. 1.70          -> width 0.05 turns")
print(f"    handedness inverts: -0.80 .. +0.86     -> the SIGN is not fixed")
worst = max(rf(class_k_pin(rsub(v, targ))[1]) for _, v in cands)
print(f"  worst candidate deviation = {worst:.5f} turns")
print(f"  -> ALL candidates sit inside the CANONICAL-ONLY band; every one of")
print(f"     them sits ~14x inside the real physical spread. The target")
print(f"     DISCRIMINATES NOTHING. Any fit is unfalsifiable. [NULL]")
import sys
sys.path.insert(0, r"D:\GitHub\mlehaptics\docs\srmech\python")
def gcd(a,b):
    while b: a,b=b,a%b
    return a
def rnorm(n,d):
    if d<0: n,d=-n,-d
    g=gcd(n if n>=0 else -n,d); return (n//g,d//g) if g else (n,d)
def radd(x,y): return rnorm(x[0]*y[1]+y[0]*x[1],x[1]*y[1])
def rsub(x,y): return rnorm(x[0]*y[1]-y[0]*x[1],x[1]*y[1])
def rf(x): return x[0]/x[1]
def pin(x):  # Class-K, not abs()
    n,d=x
    return (-1,(-n,d)) if n<0 else ((1,(n,d)) if n>0 else (0,(0,1)))

print("C6 -- do the three OA accounts CLOSE their own Lk = Tw + Wr ledger?")
print("     (each row: which member is HELD, the other two, and the residual)")
print()
rows = [
 ("classical textbook", "Lk ASSUMED -1.0", (-17,10), (7,10), (-1,1)),
 ("Segura 2018 (measured Lk)", "Lk MEASURED -1.26", (-146,100), (2,10), (-126,100)),
 ("Segura 2018 (geometric Wr)", "Wr from n=1.65,d=4deg", (-153,100), (2,10), None),
 ("Nikitina 2017 (counterfactual)", "Tw HELD at 0", (-17,10), (0,1), (-17,10)),
]
print(f"  {'account':<32}{'regime':<26}{'Wr':>8}{'Tw':>7}{'Lk_stated':>11}{'Lk_closed':>11}{'resid':>8}")
for name, regime, Wr, Tw, Lk in rows:
    closed = radd(Wr, Tw)
    if Lk is None:
        print(f"  {name:<32}{regime:<26}{rf(Wr):>8.3f}{rf(Tw):>7.2f}{'--':>11}{rf(closed):>11.3f}{'n/a':>8}")
    else:
        r = rsub(Lk, closed); _, m = pin(r)
        print(f"  {name:<32}{regime:<26}{rf(Wr):>8.3f}{rf(Tw):>7.2f}{rf(Lk):>11.3f}{rf(closed):>11.3f}{rf(m):>8.3f}")
print()
print("  Every ledger CLOSES exactly (residual 0) -- as it must: Lk=Tw+Wr is a THEOREM.")
print("  => the closure condition CANNOT falsify anything. The accounts differ only in")
print("     WHICH MEMBER IS HELD / ASSUMED, and in whether Lk is MEASURED or POSTULATED.")
print()
print("  The one GENUINE factual disagreement, isolated:")
g = rsub((-126,100), (-1,1)); _, gm = pin(g)
print(f"    classical POSTULATES Lk = -1.00 ; Segura MEASURES Lk = -1.26")
print(f"    gap = {rf(gm):.2f} turns -- this is NOT a frame choice, it is an")
print(f"    assumption vs a measurement. The frame reading does NOT dissolve it.")
print()
print("  Geometric-vs-measured gap inside Segura's own account:")
g2 = rsub((-126,100), radd((-153,100),(2,10))); _, g2m = pin(g2)
print(f"    Wr_geom(-1.53) + Tw(+0.20) = {rf(radd((-153,100),(2,10))):.2f}  vs measured Lk = -1.26")
print(f"    gap = {rf(g2m):.2f} turns, which Segura attributes to DNA breathing")
print(f"    (i.e. the wrap n is NOT 1.65 in solution -- Q1's variance, re-entering here)")
def gcd(a,b):
    while b: a,b=b,a%b
    return a
def rnorm(n,d):
    if d<0: n,d=-n,-d
    g=gcd(n if n>=0 else -n,d); return (n//g,d//g) if g else (n,d)
def rmul(x,y): return rnorm(x[0]*y[0],x[1]*y[1])
def rsub(x,y): return rnorm(x[0]*y[1]-y[0]*x[1],x[1]*y[1])
def rf(x): return x[0]/x[1]
def pin(x):
    n,d=x
    return (-1,(-n,d)) if n<0 else ((1,(n,d)) if n>0 else (0,(0,1)))

SP = (21,2)  # 10.5 bp per contact == one DNA helical turn in solution

print("C7 -- STRUCTURE-AWARE contact-quantisation (vs the structure-BLIND C3 null)")
print("     octamer contact inventory (standard accounting, TO BE ATTESTED):")
print("       4 histone-fold dimers x 3 minor-groove contacts = 12")
print("       + 2 H3 alphaN contacts at the DNA entry/exit    =  2")
print("       -------------------------------------------------  14")
print()
print(f"  {'particle':<26}{'contacts':>9}{'pred bp':>9}{'obs bp':>12}{'resid':>9}{'hit?':>6}")
cases = [
 ("octamer NCP",            14, "147",      (147,1)),
 ("hexasome (-1 H2A-H2B)",  11, "110-120",  (115,1)),
 ("tetrasome (H3-H4)2",      6, "~70",      (70,1)),
 ("chromatosome (+H1)",     16, "166-167",  (167,1)),
 ("H2A.B (predict 10)",     10, "103",      (103,1)),
 ("H3-H4 octasome",         11, "~120",     (120,1)),
]
hits = 0
for name, k, obs_s, obs in cases:
    pred = rmul((k,1), SP)
    r = rsub(obs, pred); _, m = pin(r)
    hit = rf(m) <= 5.25          # within half a contact spacing
    hits += 1 if hit else 0
    print(f"  {name:<26}{k:>9}{rf(pred):>9.1f}{obs_s:>12}{rf(r):>9.1f}{'YES' if hit else 'no':>6}")
print(f"\n  {hits}/{len(cases)} within half a contact-spacing (5.25 bp).")
print("  CAVEAT (load-bearing): the contact count k is itself read OFF the same")
print("  structures the bp count comes from -> partly CIRCULAR. The prediction is")
print("  non-circular ONLY where k is fixed independently (e.g. by which histone")
print("  fold is deleted). Hexasome/tetrasome/chromatosome ARE such cases; the")
print("  H2A.B row is a PREDICTION (k=10) not a retrodiction.")

print()
print("=" * 74)
print("C8 -- NUMEROLOGY HAZARD CHECK: 14 contacts vs the framework's 14 A-N classes")
print("=" * 74)
an        = [1,3,7,3]
nucleo    = [3,3,3,3,2]
nucleo_alt= [12,2]
def show(tag, p):
    print(f"  {tag:<34}{'+'.join(map(str,p)):<16}= {sum(p)}")
show("A-N primitive partition", an)
show("nucleosome, by histone-fold dimer", nucleo)
show("nucleosome, minor-groove + alphaN", nucleo_alt)
print()
print("  Both total 14. Are the PARTITIONS the same multiset?")
print(f"    sorted(A-N)       = {sorted(an)}")
print(f"    sorted(nucleosome)= {sorted(nucleo)}")
print(f"    EQUAL? {sorted(an)==sorted(nucleo)}")
print()
print("  VERDICT: the totals coincide; the PARTITIONS DO NOT. 1+3+7+3 has a 7;")
print("  the nucleosome inventory has no part larger than 3. Cascade-matching")
print("  compares SHAPE, not cardinality -- so this is a coincidence of small")
print("  integers, NOT a match. [NULL -- numerology hazard explicitly cleared]")


# ===================================================================== A4 / A5
# Added 2026-07-19 after the F-b hunt returned Chen et al. 2010 (PMC2887952).
print()
print("=" * 78)
print("A4 -- does the Chen 2010 (PMC2887952) SLk ledger close as QUOTED?")
print("=" * 78)
SLk = (-18, 10)
stated_Lk = (-1, 1)
for tag, phi in [("phi = -0.8  (AS QUOTED)", (-8, 10)),
                 ("phi = +0.8  (sign flipped)", (8, 10))]:
    tot = radd(SLk, phi)
    resid = rsub(stated_Lk, tot)
    _, m = class_k_pin(resid)                      # Class-K, not abs()
    ok = "CLOSES" if (m[0] == 0) else "DOES NOT CLOSE"
    print(f"  dSLk({rf(SLk):+.1f}) + {tag:<28} = {rf(tot):+.2f}"
          f"   vs stated dLk = -1.00  -> {ok}")
print("  VERDICT: the sentence as extracted does NOT close arithmetically.")
print("  'compensated' requires OPPOSITE signs; +0.8 closes exactly.")
print("  => magnitude 0.8 usable; SIGN as printed is NOT. Do not rest on -0.8.")

print()
print("=" * 78)
print("A5 -- four DISTINCT quantities are reported as bare numbers near 1-2")
print("=" * 78)
taxonomy = [
    ("1.2 / 1.5 / 1.65 / 1.7 / 1.9", "variant wraps",              "superhelical turns"),
    ("1.8",                          "Chen 2010; dSLk = -1.8",     "SURFACE LINKING / wrapping no."),
    ("-1.53",                        "Wr = n(1 - sin d)",          "WRITHE"),
    ("-1.26 / -1.00",                "per-nucleosome meas./post.", "LINKING difference"),
]
print(f"  {'value':<30}{'context':<30}{'QUANTITY'}")
for v, c, q in taxonomy:
    print(f"  {v:<30}{c:<30}{q}")
print("  The 1.8 is NOT a sixth measurement of the wrap -- it is a DIFFERENT")
print("  QUANTITY. Part of the apparent 'disagreement about 1.65' is the same")
print("  frame confusion this spike is about, present in the SOURCE literature.")


# ======================================================================= D / D5
# Added 2026-07-19 (F-h resolution). Regime (iii) is a DERIVED first-class
# result; this block is the checkable form of the derivation in note 4.4.0.
print()
print("=" * 78)
print("D -- regime (iii) DERIVED: do the premises ENTAIL it?")
print("=" * 78)
print("  P1 [ATTESTED] Wr = W[A], a functional of the AXIS CURVE ALONE.")
print("  P2 [ATTESTED] Lk = Tw + Wr, for a CLOSED ribbon.")
print("  P3 [ATTESTED] the octamer's 14 contacts pin the DNA axis path.")
print("  D1  P1 => fixing A fixes Wr. DIRECTION: {A fixed} => {Wr fixed} is")
print("      SUFFICIENT, not necessary (distinct axes can share a writhe).")
print("      Only sufficiency is needed to EXHIBIT a realization. Valid.")
print("  D2  P2 with Wr const:  dLk = dTw + 0  =>  dLk = dTw EXACTLY.")
print("      Lk and Tw co-vary one-for-one. That IS regime (iii).")
print("  D3  D1+D2 use NO biology -- mathematically well-posed on the theorem")
print("      plus the axis-only dependency alone.")
print("  D4  P3 => the nucleosome realizes it PHYSICALLY, approximately;")
print("      Q1's breathing/variance is the size of that approximation.")
print("  Inherited condition: closure -- the SAME one regimes (i)/(ii) inherit.")
print("  ENTAILMENT: mathematical claim ENTAILED; physical claim APPROXIMATE.")

print()
print("  CONSISTENCY TEST -- regime (iii) against Segura's own data:")
Wr_geom, Lk_meas, Tw_stated = (-153, 100), (-126, 100), (2, 10)
Tw_implied = rsub(Lk_meas, Wr_geom)              # dTw = dLk - Wr
resid = rsub(Tw_implied, Tw_stated)
_, rm = class_k_pin(resid)                       # Class-K, not abs()
print(f"    hold Wr = {rf(Wr_geom):+.2f}; measured dLk = {rf(Lk_meas):+.2f}")
print(f"    => dTw implied = dLk - Wr = {Tw_implied} = {rf(Tw_implied):+.3f}")
print(f"       Segura's stated dTw     = {rf(Tw_stated):+.3f}")
print(f"       residual                = {rf(rm):.3f}")
print("    The residual is NOT new: it is the SAME breathing gap isolated in")
print("    note section 2.4. Regime (iii) reproduces the known ledger and its")
print("    residual lands on a term the literature already names. CONSISTENT.")


# ======================================================================= S2 DOWN
# Added 2026-07-19. Independent re-derivation of the STRUCTURAL claims behind the
# S2 downgrade. The sigma figures themselves belong to the open-experiments spike
# and its own provenance script; these are the checks reproducible from here.
print()
print("=" * 78)
print("S2-DOWN -- structural checks behind the S2 downgrade")
print("=" * 78)
print("  datum [PMC4623960, CC BY]: tetrasome dLk is BISTABLE,")
print("  -0.80 +/- 0.05  and  +0.86 +/- 0.39 turns, barrier 2.3 +/- 0.4 kBT")
print()
print("  CHECK 1 -- can any law LINEAR IN N absorb both residuals?")
pts = [("canonical",              (147, 1), (53, 1000)),
       ("tetrasome (-0.80)",      (70, 1), (-175, 1000)),
       ("tetrasome (+0.86)",      (70, 1), (-237, 1000))]
cs = []
for nm, N, r in pts:
    c = rdiv(r, N); cs.append((nm, c))
    print(f"    {nm:<22}N={rf(N):>5.0f}  resid={rf(r):>+7.3f}  c=resid/N={rf(c):>+10.6f}")
c_can = cs[0][1]
for nm, c in cs[1:]:
    _, m = class_k_pin(rsub(c, c_can))           # Class-K, not abs()
    print(f"    c(canonical) vs c({nm.split()[0]}): differ by {rf(m):.6f}")
print("    Residual is POSITIVE at N=147, NEGATIVE at N=70. A term c*N is")
print("    monotone in N and cannot change sign between two positive N.")
print("    => NO law linear in N fits both. CONFIRMED.")
print()
print("  CHECK 2 -- arity: can a SINGLE-VALUED law produce this particle?")
bA, bB = (-80, 100), (86, 100)
_, sm = class_k_pin(rsub(bB, bA))
print(f"    branch separation = {rf(sm):.2f} turns at the SAME k")
print("    S2 is a FUNCTION k -> dLk: one input, ONE output.")
print("    => S2 cannot represent the particle AT ALL. STRUCTURAL failure;")
print("       no re-parameterisation fixes arity.")
print()
print("  CHECK 3 -- diagnosis (NOT a rescue)")
_, mA = class_k_pin(bA); _, mB = class_k_pin(bB)
_, dm = class_k_pin(rsub(mB, mA))
print(f"    |A|={rf(mA):.2f}  |B|={rf(mB):.2f}  magnitude difference={rf(dm):.2f}")
print("    Near-equal magnitude, opposite sign = the '+/- pair' of")
print("    subharmonic_chirality_carrier_findings.md 1-2. S2 is a")
print("    MAGNITUDE-ONLY law with no chirality DoF. This NAMES the failure;")
print("    it does NOT repair it. S2 stays DEGRADED.")
print()
print("  A1 REINFORCED: the sigma miss CAN be absorbed by re-choosing unattested")
print("  auxiliary scalings -- and that freedom IS A1. A hypothesis that cannot")
print("  be falsified is not passing a test when it survives one.")
