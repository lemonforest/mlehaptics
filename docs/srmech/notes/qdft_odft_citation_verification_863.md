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
