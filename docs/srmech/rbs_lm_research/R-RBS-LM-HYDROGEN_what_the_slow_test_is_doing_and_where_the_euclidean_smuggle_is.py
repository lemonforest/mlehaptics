#!/usr/bin/env python3
"""F1347 — what `hydrogen_radial` actually does, and where the Euclidean smuggle is.

User (2026-08-15): the test suite has a hydrogen_radial that eats a lot of time. Inspect
what it is and how it does it; find out whether it follows A-N grammar; check it is not
"smuggling in euclidian space geometry when cyclic group relational stuff is what makes
those euclidian rules emergent."

The contrast case is `lattice_momentum` in the SAME qm layer, whose shipped explanation
says outright: "Per [[user_stance_pi_as_projection]] it is the discrete-cyclic UPSTREAM of
the continuous derivative, not an approximation to it." That op is PERIODIC. hydrogen_radial
is DIRICHLET. This script measures what that difference costs.

srmech 0.9.0rc434. No abs(), no numpy, no RNG.
"""
import time
from srmech.math.mat import Mat
from srmech.physics.qm.potentials import hydrogen_radial
from srmech.physics.qm.single_particle import lattice_momentum, tise_solve
import srmech.math.rational as R

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<62} {got}")
    if not ok:
        FAILED.append(label)
    return ok


def build_H(n_grid, r_max=40.0, l_quantum=0):
    """The Hamiltonian hydrogen_radial builds, reproduced from potentials.py:105-118."""
    dr = r_max / (n_grid + 1)
    r = [(i + 1) * dr for i in range(n_grid)]
    inv_2dr2 = 1.0 / (2.0 * dr * dr)
    lc = l_quantum * (l_quantum + 1)
    rows = [[0.0] * n_grid for _ in range(n_grid)]
    for i in range(n_grid):
        ri = r[i]
        rows[i][i] = 2.0 * inv_2dr2 + lc / (2.0 * ri * ri) - 1.0 / ri
        if i + 1 < n_grid:
            rows[i][i + 1] = -inv_2dr2
            rows[i + 1][i] = -inv_2dr2
    return rows


print("=" * 82)
print("1 - WHAT IT IS: a TRIDIAGONAL operator carried in a DENSE n x n container")
print("=" * 82)
for n in (40, 120, 400):
    rows = build_H(n)
    nz = sum(1 for i in range(n) for j in range(n) if rows[i][j] != 0.0)
    cells = n * n
    print(f"    n_grid={n:<4} nonzeros {nz:<6} of {cells:<7} cells"
          f"   density {nz}/{cells} = {R.best_rational(nz, cells, 1000)}")
_H400 = build_H(400)          # hoisted: calling build_H INSIDE the comprehension
                              # rebuilt a 400x400 matrix 160,000 times (my bug)
ck("the operator is tridiagonal: nonzeros == 3n-2",
   sum(1 for row in _H400 for v in row if v != 0.0), 3 * 400 - 2)

print("""
  n_grid=400 is the DEFAULT. 1198 nonzeros in 160000 cells — 99.25% of the container
  is zero, and every one of those zeros is visited by a dense eigendecomposition.
""")

print("=" * 82)
print("2 - AND IT IS CARRIED AS COMPLEX, ON PROVABLY REAL DATA")
print("=" * 82)
rows = build_H(40)
allreal = all(isinstance(rows[i][j], float) for i in range(40) for j in range(40))
sym = all(rows[i][j] == rows[j][i] for i in range(40) for j in range(40))
ck("the built Hamiltonian is entirely real", allreal, True)
ck("...and symmetric", sym, True)
print("""    potentials.py:119   H = Mat.from_rows(rows, is_complex=True)
    potentials.py:127   [[eigvecs_mat[i, j].real for j in ...] ...]

  It is promoted to COMPLEX to enter mat_hermitian_eigendecompose, then the imaginary
  part is discarded at the end. The docstring says so itself: "H here is real-symmetric,
  so the eigenvectors are real". Every multiply inside the solve is a complex multiply
  on data with a zero imaginary part.
""")

print("=" * 82)
print("3 - THE COST CURVE")
print("=" * 82)
prev = None
for n in (40, 60, 80, 120):
    t = time.perf_counter(); hydrogen_radial(n_grid=n, r_max=40.0); dt = time.perf_counter() - t
    ratio = f"  x{dt/prev:.1f} for x{n/prev_n:.2f} n" if prev else ""
    print(f"    n_grid={n:<4} {dt:6.3f}s{ratio}")
    prev, prev_n = dt, n
print("""
  Superlinear, and the DEFAULT is n_grid=400 — an order of magnitude beyond the largest
  sampled here. The cost is a general dense Hermitian eigendecomposition (Jacobi sweeps)
  applied to a matrix that is 99% zeros and entirely real.
""")

print("=" * 82)
print("4 - THE CONTRAST CASE: lattice_momentum IS cyclic, and it shows")
print("=" * 82)
n = 8
P = lattice_momentum(n)
# circulant test: every entry depends only on (j - i) mod n
circ = all(P[i, j] == P[0, (j - i) % n] for i in range(n) for j in range(n))
ck("lattice_momentum is CIRCULANT (entry depends only on (j-i) mod n)", circ, True)

Hrows = build_H(n)
hcirc = all(Hrows[i][j] == Hrows[0][(j - i) % n] for i in range(n) for j in range(n))
ck("hydrogen_radial's H is CIRCULANT", hcirc, False)

# lattice_momentum's spectrum is a CLOSED FORM: the characters of Z/n
spec = sorted(tise_solve(P)[0][k, 0] for k in range(n))
closed = sorted(float(R.sin(6.283185307179586 * k / n)) for k in range(n))
worst = max((a - b) if a > b else (b - a) for a, b in zip(spec, closed))
ck("its spectrum matches the CLOSED FORM sin(2*pi*k/n) to 1e-12", worst < 1e-12, True)

print(f"""       max deviation from the closed form: {worst:.2e}

  THAT is the difference the question is about, and it is structural, not stylistic:

    lattice_momentum   PERIODIC boundary -> CIRCULANT -> the cyclic group Z/n IS the
                       operator's symmetry -> its eigenvectors ARE the characters of Z/n
                       and its spectrum is sin(2*pi*k/n) in CLOSED FORM. No eigensolver
                       is needed at all; the diagonalisation is the Class-I structure.

    hydrogen_radial    DIRICHLET walls on a uniform radial grid -> NOT circulant -> no
                       cyclic group acts -> no closed form -> a general O(n^3) solve.
""")

print("=" * 82)
print("5 - BUT BE PRECISE ABOUT WHICH PART IS SMUGGLED")
print("=" * 82)
print("""  The honest split, because 'it should have abstract meaning' cuts both ways:

    T (kinetic)   tridiagonal with a CONSTANT diagonal. A Dirichlet box is not
                  acyclic -- it is the ANTISYMMETRIC SECTOR of Z/2(n+1), and its
                  eigenvectors are sin(i j pi/(n+1)), the discrete sine transform.
                  So T *is* cyclic-group native, one folding down. CLOSED FORM.

    V (potential) diagonal, NON-constant: l(l+1)/(2 r^2) - 1/r. Diagonal in the
                  position basis, trivially.

    H = T + V     diagonal in NEITHER basis. That is not a modelling failure -- it is
                  what makes hydrogen hydrogen rather than a free particle. A bound
                  state is precisely the thing whose operator shares no eigenbasis
                  with its kinetic term.

  SO: the PHYSICS genuinely needs a general solve. The SMUGGLE is not in the maths --
  it is in the CARRIER. Three costs are paid that the structure does not require:
      (a) a tridiagonal held in a dense n x n container (99.25% zeros at the default)
      (b) complex arithmetic on provably real-symmetric data
      (c) a general dense eigensolver where the operator is tridiagonal, for which
          Sturm-sequence bisection gives eigenvalues without touching the zeros
  None of (a)-(c) is Euclidean geometry smuggled into the maths. All three are
  EUCLIDEAN-SHAPED STORAGE smuggled into the carrier -- a dense grid-of-cells standing
  in for a relational object that has 3n-2 relationships.
""")

print("=" * 82)
print("6 - THE A-N GRAMMAR GAP")
print("=" * 82)
from srmech.introspect.tool_schema import get_tool_schema
import srmech.dsl as D
e = get_tool_schema().resolve_all("hydrogen_radial")[0]
ck("no cascade descriptor exists for it",
   [o for o in D.list_cascade_ops() if "hydro" in o], [])
ck("it declares NO lane (index / sign / both)", e.reads_lane, None)
ck("it declares NO frame scope", e.frame_scope, None)
print(f"       composes: {e.composes}")
print("""
  So it is a physics op that names ONE Class-L primitive and declares nothing about
  which lane it reads or which frame it stands in -- while the operator it builds is a
  Class-I object (a cyclic difference stencil) wearing a Class-L coat. The cascade
  descriptor written alongside this script states the grammar it actually has.
""")

print("=" * 82)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 82)
raise SystemExit(1 if FAILED else 0)
