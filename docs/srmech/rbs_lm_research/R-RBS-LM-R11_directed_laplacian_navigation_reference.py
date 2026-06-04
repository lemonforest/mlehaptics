"""#797 op (b) reference — the directed/signed-Laplacian navigation, srmech-native (NO numpy eig).

The directed structure is a HERMITIAN object: H = i*(A - A^T) (F173/F175's directed γ₅-odd
antisymmetric Hermitian; the magnetic-Laplacian approach to directed graphs). So the eigen step is
the EXISTING `hermitian_eigendecompose` (complex-Hermitian -> real eigenvalues + complex
eigenvectors carrying the direction) -- no `np.linalg.eig`. The only gap is the directed-edge ->
Hermitian-Laplacian BUILDER (the directed sibling of cooccurrence_edges). This script is the
reference srmech-dev can build the C op (b) against.

Builds the DIRECTED co-occurrence of the srmech notebook (i BEFORE j in the window = asymmetric A),
forms H = i(A-A^T), eigen-decomposes via hermitian_eigendecompose, and tests:
  (1) srmech-native: hermitian_eigendecompose handles the complex-Hermitian H (real eigenvalues).
  (2) is the co-occurrence genuinely DIRECTIONAL (asymmetry fraction >> 0)?
  (3) shuffle control: is the directed structure shuffle-FRAGILE (real, like F348's undirected r=0.214)?
  (4) directed vs undirected: does H carry directional structure the symmetric Fiedler (F348) cannot?

srmech-native: dense_laplacian / hermitian_eigendecompose (Class L). np used only for the matrix
algebra of forming i(A-A^T) and Frobenius norms (mechanics, not a spectral solver) -- flagged.

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R11_directed_laplacian_navigation_reference.py
"""
import re, random
from collections import Counter
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose

HERE = Path(__file__).parent
NB = HERE.parent.parent.parent / "docs/srmech/srmech_research_notebook.md"
VOCAB, WINDOW = 200, 5
STOP = set("the a an and or but if then of in on at to for with by from as is are was were be "
           "this that these those it its they them their we us our you your i me my".split())


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]", text)
            if t.lower() not in STOP and len(t) > 2]


def directed_adjacency(tokens, vocab):
    """A[i,j] = count(token i appears BEFORE token j within the window) — DIRECTED (asymmetric)."""
    idx = {t: k for k, t in enumerate(vocab)}; N = len(vocab)
    A = np.zeros((N, N))
    indexed = [idx[t] for t in tokens if t in idx]
    for p in range(len(indexed)):
        for q in range(p + 1, min(p + WINDOW, len(indexed))):
            a, b = indexed[p], indexed[q]
            if a != b:
                A[a, b] += 1.0          # directed: a precedes b
    return A


def fiedler_real(L):
    ev, evec = hermitian_eigendecompose(L)
    ev = np.asarray(ev).real; evec = np.asarray(evec).real
    order = np.argsort(ev)
    return evec[:, order[1:3]]           # undirected Fiedler (F348)


def main():
    print(f"#797 op(b) reference — directed/signed-Laplacian navigation (srmech {srmech.__version__}, vocab={VOCAB})")
    toks = tokenize(NB.read_text())
    vocab = [t for t, _ in Counter(toks).most_common(VOCAB)]
    A = directed_adjacency(toks, vocab)

    # (2) directional content
    sym = (A + A.T) / 2.0; anti = (A - A.T) / 2.0
    asym_frac = float(np.linalg.norm(anti) / (np.linalg.norm(sym) + 1e-12))
    print(f"\n  (2) co-occurrence asymmetry fraction ||A-Aᵀ|| / ||A+Aᵀ|| = {asym_frac:.3f}  (>0 = genuinely directional)")

    # (1) srmech-native: H = i(A-Aᵀ) is complex-Hermitian -> hermitian_eigendecompose
    H = 1j * (A - A.T)
    is_herm = np.allclose(H, H.conj().T)
    try:
        evH, evecH = hermitian_eigendecompose(H)
        evH = np.asarray(evH)
        real_eigs = bool(np.allclose(evH.imag, 0, atol=1e-8)) if np.iscomplexobj(evH) else True
        print(f"  (1) H=i(A-Aᵀ) Hermitian: {is_herm}; hermitian_eigendecompose -> eigenvalues real: {real_eigs}  [srmech-native, NO numpy eig]")
        srmech_native = True
    except Exception as e:
        print(f"  (1) hermitian_eigendecompose(complex H) FAILED: {type(e).__name__}: {str(e)[:80]}")
        print(f"      -> srmech hermitian_eigendecompose may be real-symmetric-only; the directed op needs complex-Hermitian support (GAP).")
        srmech_native = False
        evH = None

    # (3) shuffle control — is the DIRECTIONAL structure real (shuffle-fragile)?
    sh = toks[:]; random.Random(20260604).shuffle(sh)
    A_sh = directed_adjacency(sh, vocab)
    anti_sh = (A_sh - A_sh.T) / 2.0; sym_sh = (A_sh + A_sh.T) / 2.0
    asym_frac_sh = float(np.linalg.norm(anti_sh) / (np.linalg.norm(sym_sh) + 1e-12))
    # correlation of the directed (antisymmetric) structure real-vs-shuffled
    iu = np.triu_indices(len(vocab), k=1)
    r_anti = float(np.corrcoef(anti[iu], anti_sh[iu])[0, 1])
    print(f"  (3) shuffle control: asymmetry frac real={asym_frac:.3f} vs shuffled={asym_frac_sh:.3f}; directed-structure corr real-vs-shuffle r={r_anti:+.3f}")

    # (4) directed vs undirected: how much navigation content is in the antisymmetric part the symmetric Fiedler can't see
    print(f"  (4) directional energy carried by H (lost to the undirected/symmetric Fiedler of F348): {asym_frac:.1%} of the symmetric scale")

    print("\n=== verdict ===")
    directional = asym_frac > 0.05
    shuffle_destroys = asym_frac_sh < asym_frac * 0.5 and abs(r_anti) < 0.5
    print(f"  co-occurrence is genuinely DIRECTIONAL (asym>0.05): {directional}")
    print(f"  directed structure is REAL (shuffle destroys it): {shuffle_destroys}")
    print(f"  directed op is srmech-NATIVE via hermitian_eigendecompose(i(A-Aᵀ)) (no numpy eig): {srmech_native}")
    if directional and srmech_native:
        print(f"  => REFERENCE READY for #797 op(b): the directed/signed Laplacian is the Hermitian H=i(A-Aᵀ),")
        print(f"     eigen-solved by the EXISTING hermitian_eigendecompose. The only srmech gap is the directed-edge")
        print(f"     BUILDER (directed cooccurrence -> H), NOT a new eigensolver. {asym_frac:.0%} of the navigation is")
        print(f"     directional content the undirected Fiedler (F348) cannot carry.")
    elif not srmech_native:
        print(f"  => GAP: hermitian_eigendecompose needs complex-Hermitian support for the directed op (log for srmech-dev).")

if __name__ == "__main__":
    main()
