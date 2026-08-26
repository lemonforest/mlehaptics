"""F936 (corrects F935's one-axis framing) — harmonic and subharmonic are TWO SEPARATE chiral axes
({0,+1} and {0,-1}), NOT +/-1 of one line (not time-reversal). Grounded: the triality has THREE distinct
eigenspaces (1:14, omega:7, omega^2:7) -> omega, omega^2 are two separate axes. Together with the shared
rest (0 = eigenvalue 1 = the g2-fixed generate), the three values are BALANCED TERNARY = the TRIT = Z3.
The substrate is ternary; 'reduce to linear form' = collapse the trit to binary. srmech rc58; from F932 traces."""
from fractions import Fraction as Fr
tr0,tr1,tr2 = 28, 7, 7                  # tr(I), tr(tau), tr(tau^2)  (F932, tau order-3)
m1, mw, mw2 = Fr(tr0+tr1+tr2,3), Fr(tr0-tr1,3), Fr(tr0-tr2,3)   # using omega+omega^2 = -1
print(f'triality eigenspaces: 1 -> mult {m1} | omega -> {mw} | omega^2 -> {mw2}  (sum {m1+mw+mw2})')
print('  three DISTINCT eigenspaces; omega(7) and omega^2(7) are TWO SEPARATE axes (the correction).')
print('  balanced-ternary trit {-1,0,+1}:  0<->1 (mult14, g2-fixed GENERATE/our-sector rest);')
print('                                    +1<->omega (mult7, HARMONIC axis {0,+1});')
print('                                    -1<->omega^2 (mult7, SUBHARMONIC axis {0,-1}).')
print('  => substrate is Z3 / TERNARY (the trit); linear/binary reduction loses a chiral axis = the snapshot.')
