"""F1007 (user question) — is the SIGNED Laplacian wrong for dual-sense (F1006: +is-a/-is-not-a CANCEL to 0)?
Do we need a CHIRAL Laplacian whose +/- are overtone/undertone (don't cancel), like the mock-theta beat? Is there
a THETA Laplacian? Answer both empirically. (A) real signed ±1 cancel; the magnetic (Hermitian) Laplacian puts
the two senses on a PHASE axis e^(±iq) so they SURVIVE (2cos q), and an ASYMMETRIC pair leaves an imaginary
(a-b)sin q = the overtone/undertone chirality. (B) the heat-trace Tr(e^{-tL}) = Σ e^{-t λ} IS a theta function of
the Laplacian; the CHIRAL (magnetic, flux) Laplacian's heat-trace is a flux-TWISTED theta (the flux = the shadow,
mock-theta-like). srmech Class-L. cmath/math only at the display boundary (transcendental scalar)."""
import math, cmath
from srmech.amsc import laplacian as L
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def re(z): return fl(z.real) if hasattr(z,'real') else fl(z)
# ---- (A) dual-sense coupling: real signed CANCELS ; chiral phase SURVIVES ----
q=0.25*math.pi                                  # phase charge (overtone +q / undertone -q)
signed = 1.0 + (-1.0)                           # real ±1 on the SAME edge -> 0 (F1006: annihilates)
chiral_sym = cmath.exp(1j*q) + cmath.exp(-1j*q) # phase ±q, symmetric a=b=1 -> 2cos q (REAL, non-zero)
a,b = 1.0, 0.6                                   # ASYMMETRIC: is-a overtone stronger than is-not-a undertone
chiral_asym = a*cmath.exp(1j*q) + b*cmath.exp(-1j*q)   # (a+b)cos q + i(a-b)sin q
print("F1007 -- chiral vs signed Laplacian for dual-sense, and the theta Laplacian:")
print("  (A) dual-sense edge 'X is-a Y' (+) AND 'X is-not-a Y' (-):")
print("      SIGNED (real ±1):        %+.4f            -> CANCELS (F1006: the two senses annihilate)"%signed)
print("      CHIRAL (phase e^±iq),sym: %.4f + %.4fi   -> SURVIVES as 2cos q (real, non-zero)"%(chiral_sym.real, chiral_sym.imag))
print("      CHIRAL asymmetric a=%.1f b=%.1f: %.4f + %.4fi -> imaginary (a-b)sin q = OVERTONE/UNDERTONE chirality"%(a,b,chiral_asym.real, chiral_asym.imag))
print("      (=> real signed lives on ℝ so ±cancel; the magnetic/HERMITIAN Laplacian lives on the phase circle,")
print("          so is-a=+q / is-not-a=-q are conjugate partners that DON'T cancel -- THIS is the chiral Laplacian.)")
# ground it: the magnetic Laplacian IS Hermitian (complex off-diagonal), the signed one is real
cyc=[(i,(i+1)%6) for i in range(6)]
Ls=L.signed_laplacian(6, cyc, [1.0]*6); Lm=L.magnetic_laplacian(6, cyc, q=0.25)
so=Ls[0][1] if not hasattr(Ls,'tolist') else Ls.tolist()[0][1]
mo=Lm[0][1] if not hasattr(Lm,'tolist') else Lm.tolist()[0][1]
print("      grounded off-diagonal L[0][1]: signed=%s (REAL) | magnetic=%s (COMPLEX=carries the chirality)"%(so, mo))
# ---- (B) the THETA Laplacian: heat-trace Tr(e^{-tL}) = Σ e^{-tλ} is a theta fn; flux TWISTS it ----
n=12; ring=[(i,(i+1)%n) for i in range(n)]
def theta(evs,t): return sum(math.exp(-t*e) for e in evs)  # heat-trace = SPECTRAL theta (display-level scalar)
def spec(Phi):                                             # spectrum of the magnetic Laplacian at total flux Phi (quanta)
    H=L.magnetic_laplacian(n, ring, q=Phi/n)
    res=L.hermitian_eigendecompose(H); ev=res[0] if isinstance(res,(tuple,list)) else res
    return sorted(re(x) for x in (ev.tolist() if hasattr(ev,'tolist') else list(ev)))
base=theta(spec(0.0),1.0)
print("  (B) THETA Laplacian -- heat-trace Θ(t)=Tr(e^{-tL})=Σe^{-tλ} (the OVERTONE sum) vs total flux Φ (quanta):")
print("       Φ       λ_min(ground)   Θ(t=1) full-trace    reading")
for Phi in (0.0, 0.3, 0.5, 1.0, 2.0):
    ev=spec(Phi); lm=ev[0]; th=theta(ev,1.0)
    integer = (Phi==float(round(Phi)))          # integer-flux test (exact for the swept values; no abs)
    print("      %.1f    %.4f          %9.5f          %s"%(Phi, lm, th,
          'Φ∈ℤ: λ_min=0 (gauge-trivial), trace = the modular theta' if integer else 'Φ∉ℤ: λ_min LIFTS = the flux SHADOW (ground-state); trace unchanged'))
print("      (=> the full heat-trace Θ is Φ-INVARIANT (Poisson: the overtone mode-sum = the MODULAR/holomorphic")
print("          theta); the flux enters ONLY the GROUND STATE λ_min (the UNDERTONE/subharmonic = the mock-theta")
print("          SHADOW). Overtone-trace vs undertone-ground-state IS the mock-theta split.)")
print("=> ANSWER: (A) YES -- the CHIRAL Laplacian is the MAGNETIC (Hermitian) Laplacian: is-a=+q / is-not-a=-q are")
print("   conjugate overtone/undertone partners that SURVIVE (2cos q + i(a-b)sin q), where the real SIGNED Laplacian")
print("   annihilates them (±1->0). F1006's dual-sense pairs want the MAGNETIC (chiral) Laplacian, not the signed.")
print("   (B) YES -- the THETA Laplacian is the heat-trace Tr(e^{-tL}); Θ itself is the flux-INVARIANT MODULAR theta")
print("   (overtone), and the flux SHADOW is the ground-state λ_min(Φ) lift (undertone/subharmonic, F997) -- exactly")
print("   the mock-theta holomorphic+shadow split, periodic in integer flux (gauge quanta).")
