/*
 * srmech_spectral_codec.c — spectral decompose / recompose projection C peers
 * (v0.9.0rc219; gh #827 — the encode-pipeline's other half).
 *
 * The C mirror of the per-state half of `srmech.spectral.decompose` /
 * `recompose` — the eigenbasis projection an encode stream pays PER STATE
 * once the substrate eigendecomposition is cached:
 *
 *   - srmech_spectral_decompose : coeffs = Vᴴ·state, plus the complex128
 *                                 coefficient-byte pack and the Class-A
 *                                 content sha over those bytes, in ONE call
 *   - srmech_spectral_recompose : state = V·coeffs (the inverse projection)
 *
 * Profile-first rationale (#827): with the eigenbasis CACHED (the enwiki
 * steady state) the measured per-state cost at n=128 was ~75 ms of Python
 * carrier→C-buffer marshalling around a µs-scale matvec (plus ~81 ms of
 * Python descriptor-hash byte-building, fixed Python-side by carrier-identity
 * memoization — NOT a C symbol). These peers take the ALREADY-COMPUTED
 * eigenvector carrier buffer zero-copy and collapse marshal + matvec + pack +
 * sha into one crossing. They deliberately do NOT re-implement (or contain)
 * the eigendecomposition — the Python wrapper keeps the existing
 * `mat_hermitian_eigendecompose` LRU cache.
 *
 * PARITY KIND (the rc218 macOS lesson made a build constraint): these are
 * FLOAT-eig-derived NUMERIC ops. On one machine the native peer is
 * byte-identical to the current native path BY CONSTRUCTION — the projection
 * runs through the SAME srmech_dense_matmul_complex kernel the rc218
 * mat_matvec route dispatches to, over the same conjugate-transpose bytes
 * (conjugation = exact imag sign-flip) — but the underlying eigenvectors
 * diverge in the last ULPs across platforms/arms, so the test contract is
 * within-tol + round-trip + same-machine kernel-equality, NEVER a hardcoded
 * cross-platform SHA.
 *
 * Composes the EXISTING public C leaves: srmech_dense_matmul_complex
 * (the contraction engine) + srmech_sha256_hex (Class A).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — loops bounded by n
 *   - Rule 3 (no malloc)      : OK — caller-arena scratch (the Vᴴ staging)
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/func): OK
 *   - Rule 8 (simple macros)  : OK — none
 *
 * No abs(): the conjugate is a Class-K exact sign-flip of the imaginary
 * slot; there is no magnitude anywhere in these kernels.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Vᴴ·state — project a node-domain state onto the eigenbasis and mint the
 * SpectralHandle byte payload. `v_interleaved` is the n×n eigenvector Mat
 * buffer (row-major interleaved (re, im); columns = eigenvectors), read
 * zero-copy and never written. `state_interleaved` is the n-element state.
 * `scratch_vh` (2*n*n doubles, caller arena) stages Vᴴ so the projection runs
 * through the SAME public srmech_dense_matmul_complex kernel the carrier
 * mat_matvec route uses — same-machine byte-identity by construction.
 * `out_coeffs` (2*n doubles) receives the coefficients — its raw bytes ARE
 * the handle's complex128 coefficients_bytes (native-endian interleaved
 * float64 pairs) — and `out_sha_hex` (65 bytes) their lowercase content sha.
 * scratch_vh / out_coeffs must not alias the inputs. */
srmech_status_t srmech_spectral_decompose(
    uint32_t       n,
    const double  *v_interleaved,
    const double  *state_interleaved,
    double        *scratch_vh,
    double        *out_coeffs,
    char          *out_sha_hex)
{
    srmech_status_t st;
    assert(v_interleaved != NULL && state_interleaved != NULL);
    assert(scratch_vh != NULL && out_coeffs != NULL && out_sha_hex != NULL);
    if (v_interleaved == NULL || state_interleaved == NULL ||
        scratch_vh == NULL || out_coeffs == NULL || out_sha_hex == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Vᴴ[i, t] = conj(V[t, i]) — exact transpose + imag sign-flip. */
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t t = 0; t < n; t++) {
            size_t src = ((size_t)t * n + i) * 2u;
            size_t dst = ((size_t)i * n + t) * 2u;
            scratch_vh[dst]      = v_interleaved[src];
            scratch_vh[dst + 1u] = -v_interleaved[src + 1u];
        }
    }
    st = srmech_dense_matmul_complex(n, n, 1u, scratch_vh,
                                     state_interleaved, out_coeffs);
    if (st != SRMECH_OK) {
        return st;
    }
    return srmech_sha256_hex((const uint8_t *)out_coeffs,
                             (size_t)n * 2u * sizeof(double), out_sha_hex);
}

/* V·coeffs — the inverse projection back to the node domain. `v_interleaved`
 * is the SAME n×n eigenvector buffer decompose read (zero-copy, unmodified);
 * `coeffs_interleaved` is the handle's coefficients_bytes viewed as 2*n
 * doubles. `out_state` (2*n doubles) receives the reconstructed node-domain
 * state. Runs through the same public matmul kernel (n×n · n×1) the carrier
 * mat_matvec route uses — same-machine byte-identity by construction.
 * out_state must not alias the inputs. */
srmech_status_t srmech_spectral_recompose(
    uint32_t       n,
    const double  *v_interleaved,
    const double  *coeffs_interleaved,
    double        *out_state)
{
    assert(v_interleaved != NULL && coeffs_interleaved != NULL);
    assert(out_state != NULL);
    if (v_interleaved == NULL || coeffs_interleaved == NULL ||
        out_state == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return srmech_dense_matmul_complex(n, n, 1u, v_interleaved,
                                       coeffs_interleaved, out_state);
}
