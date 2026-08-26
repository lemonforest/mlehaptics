"""F974 — is a half-life a ladder-rung's |q|? YES: the half-life IS the rung where |q|=1/2 EXACTLY and
UNIVERSALLY (definitional, memoryless) = the OCTAVE, the CALIBRATION UNIT for a REUSABLE |q|-meter. Any
cascade recession ratio r -> octaves = halvings-to-reach r (bit-exact, no float/abs). The meter CLASSIFIES
every cascade: CONSTANT octaves/beat = memoryless-geometric (half-life-like, ONE |q| rung); ACCELERATING =
factorial/super-geometric (multi-rung). Empirical isotope-SET-laddered test needs ATTESTED NNDC data (NOT
fabricated; flagged). srmech rc97; framework-reading of decay statistics only."""
from fractions import Fraction as Fr
def octaves(r):                       # bit-exact ceil(log2(1/r)): halvings of 1 until <= r
    r=Fr(r); n=0; x=Fr(1)
    while x>r and n<300: x=x/2; n+=1
    return n
print('CALIBRATION UNIT -- radioactive decay, |q| per half-life = 1/2 EXACT, memoryless:')
print('   1 half-life (1/2) -> %d octave  |  3 half-lives (1/8) -> %d octaves  (the UNIT ladder; constant 1/beat)'%(octaves(Fr(1,2)),octaves(Fr(1,8))))
print('REUSABLE |q|-meter on other GROUNDED cascades:')
print('   geometric q=1/3 per beat  -> %d octaves/beat (CONSTANT = memoryless-geometric, ONE |q|, half-life-like)'%octaves(Fr(1,3)))
res=[Fr(136,100000), Fr(245,10000000), Fr(273,1000000000)]   # cos-series |residue| at 2,3,4 terms (F949)
prev=None
for i in range(len(res)-1):
    ratio=res[i+1]/res[i]; o=octaves(ratio)
    print('   cos-series residue step %d->%d (ratio 1/%d) -> %d octaves  (ACCELERATING = factorial, NOT one |q|)'%(i+2,i+3,int(1/ratio),o))
print('=> half-life = the |q|=1/2 UNIT octave (constant/beat, memoryless) -> calibrates the meter.')
print('   CLASSIFIER: constant octaves/beat = half-life-like (one rung |q|); accelerating = factorial (multi-rung).')
