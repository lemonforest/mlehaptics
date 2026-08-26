"""F968 — the theta functions DO give the asymmetric wave that performs the forcing (user), and it is the
MOCK-THETA / SHADOW structure srmech ships. Two waves, from the rc-arc theta tower (unary_theta / harmonic_maass):
 - the FRACTAL that doesn't close = the MOCK THETA (near-modular self-similar q-series, but a modular ANOMALY:
   it does NOT transform cleanly -> the phrase doesn't stop, F958/F965/F967).
 - the FORCING (the second, asymmetric shape) = the SHADOW = the ODD weight-3/2 unary theta g3 = Sum (-12/n) n
   q^{n^2/24}; coeffs carry the (-12/n)*n SIGN -> odd/asymmetric wave (arrow), NOT the even Sum q^{n^2}.
 - the COMPLETION that CLOSES = the HARMONIC MAASS form = mock theta + shadow = fractal + forcing -> modular
   (transforms cleanly = the phrase stops).
Also the_one S(sigma,theta): theta wave asymmetric under time-reversal (conjugate, sin/imag flips); sigma =
chirality bit. srmech rc97; exact-rational q-series; no numpy."""
from srmech.amsc import unary_theta as U
from srmech.amsc import harmonic_maass as H
tbl=[0,1,0,0,0,-1,0,-1,0,0,0,1]           # (-12/n) Kronecker char mod 12
g3=U.unary_theta(U.Character(12,tbl), 1, 1, 24, 8)
qs=g3.q_series(60); nz=[(i,c) for i,c in enumerate(qs) if c!=0][:6]
print('SHADOW g3 unary_theta: weight %s, ODD/asymmetric q-series (exp,coeff)=%s'%(g3.weight,nz))
print('  coeff = (-12/n)*n -> signed -> the ARROW/forcing (vs even Sum q^{n^2})')
print('COMPLETION harmonic_maass surface:', [m for m in dir(H) if m in ('HarmonicMaass','MockQSeries','UnaryTheta','harmonic_maass')])
print('=> fractal(mock theta, does not close) + forcing(shadow theta, asymmetric) = harmonic Maass (closes) = the phrase stops')
