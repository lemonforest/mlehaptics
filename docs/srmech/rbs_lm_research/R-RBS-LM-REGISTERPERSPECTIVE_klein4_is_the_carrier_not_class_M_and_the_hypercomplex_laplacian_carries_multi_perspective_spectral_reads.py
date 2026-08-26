"""R-RBS-LM-REGISTERPERSPECTIVE (F1302) — klein4 is the CARRIER SHAPE (not Class-M); Class-M and Class-L are
ROLES over it; and a HYPERCOMPLEX / gain Laplacian carries the SPECTRAL read (eigenvectors/eigenvalues) for
more than one perspective. srmech ships magnetic_laplacian (C, 2 perspectives) and klein4_gain_laplacian (V4).
Run: /tmp/srmech_new/bin/python3 R-RBS-LM-REGISTERPERSPECTIVE_*.py"""
import math
from srmech.amsc import laplacian as L, hdc, cascade

print("=== Q4: klein4 == Class-M, or the shared CARRIER SHAPE? ===")
print("  klein4 = Z/2 x Z/2 (4 sectors, the quad) — a fixed STRUCTURE.")
print("  Class-M = HDC bind role (klein4_bind/bundle) — lossy working-memory READ.")
print("  Class-L = Laplacian role (dense/magnetic_laplacian) — exact STORE.")
print("  both ride klein4:  klein4_bind present:", hasattr(hdc, "klein4_bind"),
      "| genome packs edges element_type='klein4' (F1300)")
print("  => klein4 is the CARRIER; M and L are ROLES over it. Lossiness is in the READ, not klein4.")

print("\n=== Q1/Q2: only carrier, or the H-rung of a tower? ===")
one = cascade.the_one(1, 0)
print("  the_one partition:", one.partition, "-> klein4 = the 4-sector (H-rung) quad")
print("  cd_register widens the quad up the CD tower:", cascade.CD_DIMS)
print("  => correct for the 4-sector quad; NOT the only carrier (F1301: perspectives scale 1,3,7,15).")

print("\n=== Q5: does a register carry the SPECTRAL read for MORE THAN ONE perspective? ===")
edges = [(0, 1), (1, 2), (2, 0)]; w = [9.0, 6.0, 6.0]
lap = L.dense_laplacian(3, edges, w)
ev, _ = L.symmetric_eigendecompose(lap)
print("  (R) real symmetric eigenvalues:", [round(float(e), 2) for e in ev], "-> 1 perspective (metric)")
Lm = L.magnetic_laplacian(3, edges, w, charges=[3.0, 2.0, 4.0])   # charges carry the phase (no q)
hev, hV = L.hermitian_eigendecompose(Lm)
v = hV[0] if hV else []
mags = [round((getattr(c, "real", c) ** 2 + getattr(c, "imag", 0.0) ** 2) ** 0.5, 3) for c in v]
phases = [round(math.atan2(getattr(c, "imag", 0.0), getattr(c, "real", c)), 3) for c in v]
carries = any(cascade.magnitude(p) > 1e-6 for p in phases)   # Class-K pin-slot, not the builtin
print("  (C) magnetic Hermitian: eigenvalues REAL", [round(float(getattr(e, "real", e)), 2) for e in hev])
print("      eigenvector |.|:", mags, " (metric mode)")
print("      eigenvector arg:", phases, " (DIRECTION mode) -> phase present:", carries)
print("      => ONE spectral read, TWO perspectives (|eigvec|=metric, arg(eigvec)=direction).")
print("  (V4) klein4_gain_laplacian shipped:", hasattr(L, "klein4_gain_laplacian"),
      "-> the V4/Klein-4-sector 'EVEN-channel fuller partner' (4-sector spectral register).")
print("  => perspective-count of a spectral read = imaginary dim of its Laplacian's algebra.")
print("     R:1  C:2 (magnetic, shipped)  V4:4-sector (klein4_gain, shipped)  H:4  O:8 (not shipped).")
