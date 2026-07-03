# QDFT/ODFT citation pass — #863 (rc31 prerequisite)

**Verified 2026-06-04** via WebFetch against the actual abstracts/PDFs (MPM
PDF-extraction discipline). All three anchors are **OA / attestable**; the two
paywalled candidates were deliberately excluded in favour of their OA
equivalents per the paywalled-DOI rule
(`[[feedback_paywalled_doi_cannot_be_attested]]`).

## LODGE (OA, verified)

1. **QDFT anchor** — Sangwine, S. J. & Ell, T. A. (2012).
   *Complex and Hypercomplex Discrete Fourier Transforms Based on Matrix
   Exponential Form of Euler's Formula.* Applied Mathematics and Computation
   **219**(2):644–655. **arXiv:1001.4379** (submitted 2010-01-25, rev 2011-07-04).
   - Verified: title + authors + arXiv ID confirmed against arxiv.org/abs/1001.4379.
   - Why this one: builds the complex→quaternion→biquaternion→Clifford DFT ladder
     via the **matrix-exponential `exp(μθ)` Euler form** — exactly the (2:1)→(4:3)
     coefficient-algebra ladder + the `exp(μθ)` twiddle helper #863 names.

2. **ODFT anchor** — Błaszczyk, Ł. (2019).
   *A Generalization of the Octonion Fourier Transform to 3-D Octonion-Valued
   Signals — Properties and Possible Applications to 3-D LTI Partial Differential
   Systems.* **arXiv:1905.12631** (single author).
   - Verified: title + sole author (Łukasz Błaszczyk) + arXiv ID confirmed.
   - Abstract first sentence pins the origin: "…the octonion Fourier transform
     (OFT) theory initiated in 2011 in articles by Hahn and Snopek."

3. **ODFT origin** — Hahn, S. L. & Snopek, K. M. (2011).
   *The unified theory of n-dimensional complex and hypercomplex analytic
   signals.* Bulletin of the Polish Academy of Sciences: Technical Sciences
   **59**(2):167–181. (Bulletin PAS = OA.)
   - Verified: title + authors + vol/issue/pages corroborated by the Błaszczyk
     arXiv abstract + independent search; OA via the Bulletin.

## EXCLUDED (paywalled — do NOT lodge)

- Ell, T. A. & Sangwine, S. J. (2007). *Hypercomplex Fourier Transforms of Color
  Images.* IEEE Trans. Image Processing **16**(1):22–35. — **IEEE paywall**; OA
  copy (CiteSeerX/web.archive) was unfetchable. The QDFT ground it covers is
  carried OA by arXiv:1001.4379 (same authors), so lodge that instead.
- Błaszczyk, Ł. & Snopek, K. M. (2017). *Octonion Fourier Transform of
  real-valued functions of three variables — selected properties and examples.*
  Signal Processing **136**:29–37. — **Elsevier paywall**; same lead author's
  arXiv:1905.12631 carries it OA.

## rc31 use

- `quaternion_dft.toml` → cite anchor (1) in the descriptor's literature/attestation block.
- `octonion_dft.toml` → cite anchors (2)+(3); the **bracketing/association convention**
  is an explicit declared field (octonion non-associativity is a mathematical fact,
  F378 — the citations anchor the OFT *definition*, not the bracketing claim).

## rc110 re-verification (2026-07-03; #1234 Item 1b — the QDFT graduation)

Anchor (1) **re-verified FIRST-HAND** at the rc110 build (the issue-mandated
MPM gate: verify-PDF before lodging). Method: fetched the OA arXiv PDF
(`arxiv.org/pdf/1001.4379`, v3, 4 Jul 2011) and extracted its text
(pypdf, 14 pages / ~41k chars); checked against the lodged citation:

- **Title** — "Complex and Hypercomplex Discrete Fourier Transforms Based on
  Matrix Exponential Form of Euler's Formula" ✓ (page 1).
- **Authors** — Stephen J. Sangwine (Univ. of Essex) + Todd A. Ell ✓
  (page-1 footnotes).
- **arXiv ID / version** — `arXiv:1001.4379v3 [math.RA] 4 Jul 2011` ✓;
  journal ref Appl. Math. Comput. 219(2):644–655 (2012) ✓ (abs page).
- **The cited convention actually appears**: the exponential-PLACEMENT
  distinction is discussed in the body ("If the exponential were to be
  placed on the right, f and F would have to be transposed, …"), the
  one-sided quaternion DFT is referenced against the authors' own 2007
  paper ([16] §VI), and **§7 "Extension to two-sided DFTs"** covers the
  two-sided form — i.e. the one-sided/left-right/two-sided landscape the
  rc110 `quaternion_dft` documents is genuinely present in the verified
  OA source.

**Scope of the attribution (unchanged):** the paper anchors the `exp(μθ)`
matrix-exponential Euler-form hypercomplex-DFT *framework* and the
form-distinction *landscape*. The precise operational convention srmech
ships (forward σ=−1; left form `X[k]=Σ_n W(σ2πkn/N)·x[n]`, right form
`X[k]=Σ_n x[n]·W(σ2πkn/N)`; inverse σ=+1 + 1/N on the same side) is the
IN-REPO SSOT — rc109 `qm.quaternion` + the R21 proof — not an external
attribution. No new external citation was lodged at rc110.
