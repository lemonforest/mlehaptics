/*
 * srmech_dense_solve.c — Class L primitive: dense linear solve A·X = B.
 *
 * v0.7.1rc3 ([#897](https://github.com/lemonforest/mlehaptics/issues/897)
 * §26 follow-up). The reusable float64 dense linear solve that the
 * Schur-complement / Dirichlet-to-Neumann float path composes over (the
 * expensive interior solve L_ii⁻¹·L_i∂ IS an A·X = B). Promoted to its
 * own exported Class-L primitive per the "every primitive earns a C
 * surface" commitment — a dense solve is reusable (future inverse / lstsq
 * float paths) and the solve, not the matmul, is where the cost lives.
 *
 * Gauss–Jordan elimination with PARTIAL PIVOTING on an augmented [A | B]
 * working copy: at exit the augmented tail holds X directly. Partial
 * pivoting (largest-magnitude pivot at/below the diagonal) is needed for
 * float numerical stability — the exact-rational Python path needs no
 * magnitude pivot (any nonzero pivot is exact), but float does. The pivot
 * magnitude is the Class-K pin-slot read; the sign is a BRANCH, never
 * fabs() / abs() (per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]
 * and the rc46 fabs→sign-branch sweep). No transcendentals: a linear
 * solve is + − × ÷ only, so this surface routes through NO libm and NO
 * Class-N cascade (unlike the Jacobi eigensolver, which needs sqrt).
 *
 * Public API:
 *   - srmech_dense_solve_f64_ws  (A·X = B, A n×n, B/X n×nrhs, row-major;
 *                                 augmented [A|B] scratch from caller arena)
 *   - srmech_dense_solve_arena_bytes  (arena byte count for a given n, nrhs)
 *
 * Conventions:
 *   - Matrices are row-major doubles (caller-allocated). A is n×n, B is
 *     n×nrhs, out_X is n×nrhs.
 *   - A wholly-zero pivot column at/below the diagonal ⇒ singular A ⇒
 *     SRMECH_ERR_BAD_INPUT (the Python wrapper raises ZeroDivisionError;
 *     pure-Python's exact-rational Gauss–Jordan raises the same — the two
 *     are complete alternative implementations, not one rescuing the other).
 *   - NO compiled-in size cap: the augmented [A | B] working matrix is
 *     carved from a CALLER-supplied arena `ws` (srmech_dense_solve_arena_bytes
 *     sizes it), so the only bound is the caller's RAM — a host sizes it
 *     large, a microcontroller small (the v0.7.5rc154 genome caller-arena
 *     precedent / [[feedback_c_must_be_standalone_complete_no_python_fallback]]).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by n / nrhs
 *                              (≤ the MAX bounds, checked before the solve)
 *   - Rule 3 (no malloc)      : OK — the augmented buffer is bump-carved
 *                              from the caller arena `ws`; everything else
 *                              is stack scalars
 *   - Rule 4 (≤60 lines/func) : OK — solve split into load / pivot /
 *                              eliminate helpers
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 8 (no multi-line macros) : OK — single-line #defines only
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic / /W4
 *
 * ABI: the rc154 standalone-complete honor (v0.7.5rc158) RENAMES the symbol
 * to srmech_dense_solve_f64_ws (the arena-taking form) and adds
 * srmech_dense_solve_arena_bytes; the Python ctypes shim hasattr-guards the
 * new name (a stale lib lacking it falls to pure-Python), so SRMECH_ABI_VERSION
 * stays 3 — the old capped srmech_dense_solve_f64 is removed, not re-signatured.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* No compiled-in size cap (rc158 standalone-complete honor): the augmented
 * [A | B] working matrix is carved from the caller arena `ws`, sized by
 * srmech_dense_solve_arena_bytes. The bound is the caller's RAM, not a 256. */

/* Load the augmented [A | B] matrix into the working buffer. The buffer
 * has row stride w = n + nrhs: columns [0, n) hold A, [n, n+nrhs) hold B. */
static void dense_solve_load_aug(uint32_t n, uint32_t nrhs,
                                 const double *A, const double *B,
                                 double *aug)
{
    assert(A != NULL);
    assert(B != NULL);
    assert(aug != NULL);
    size_t w = (size_t)n + (size_t)nrhs;
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = 0; c < n; c++) {
            aug[(size_t)r * w + c] = A[(size_t)r * n + c];
        }
        for (uint32_t c = 0; c < nrhs; c++) {
            aug[(size_t)r * w + (size_t)n + c] = B[(size_t)r * nrhs + c];
        }
    }
}

/* Partial-pivot column `col`: find the row r >= col with the largest
 * |aug[r][col]|, swap it up to row `col`, and return that magnitude. A
 * returned 0.0 means the column is wholly zero at/below the diagonal — a
 * singular system. Magnitude is the Class-K pin-slot read; sign is a
 * branch, never fabs(). */
static double dense_solve_pivot(uint32_t n, uint32_t nrhs,
                                double *aug, uint32_t col)
{
    assert(aug != NULL);
    assert(col < n);
    size_t w = (size_t)n + (size_t)nrhs;
    uint32_t best_row = col;
    double best_mag = 0.0;
    for (uint32_t r = col; r < n; r++) {
        double v = aug[(size_t)r * w + col];
        double mag = (v < 0.0) ? -v : v;
        if (mag > best_mag) {
            best_mag = mag;
            best_row = r;
        }
    }
    if (best_row != col) {
        for (size_t c = 0; c < w; c++) {
            double tmp = aug[(size_t)col * w + c];
            aug[(size_t)col * w + c] = aug[(size_t)best_row * w + c];
            aug[(size_t)best_row * w + c] = tmp;
        }
    }
    return best_mag;
}

/* Gauss–Jordan step on pivot column `col`: normalise the pivot row by its
 * diagonal, then eliminate column `col` from every OTHER row, so the
 * augmented tail holds X directly at exit. Caller guarantees a non-zero
 * pivot (checked via dense_solve_pivot's return). */
static void dense_solve_eliminate(uint32_t n, uint32_t nrhs,
                                  double *aug, uint32_t col)
{
    assert(aug != NULL);
    assert(col < n);
    size_t w = (size_t)n + (size_t)nrhs;
    double piv = aug[(size_t)col * w + col];
    assert(piv != 0.0);
    for (size_t c = 0; c < w; c++) {
        aug[(size_t)col * w + c] /= piv;
    }
    for (uint32_t r = 0; r < n; r++) {
        if (r == col) {
            continue;
        }
        double f = aug[(size_t)r * w + col];
        if (f == 0.0) {
            continue;
        }
        for (size_t c = 0; c < w; c++) {
            aug[(size_t)r * w + c] -= f * aug[(size_t)col * w + c];
        }
    }
}

/* The arena byte count srmech_dense_solve_f64_ws needs for an n×n A and an
 * n×nrhs B: the augmented [A | B] working matrix is n rows × (n + nrhs)
 * columns of double, plus sizeof(double) slop so the bump base can be rounded
 * up to an 8-byte (double) boundary. Pure arithmetic — the caller sizes its
 * `ws` arena from THIS, so the bound is the caller's RAM, never a compiled-in
 * cap (a host sizes it large, a microcontroller small). Adding this symbol
 * does NOT bump SRMECH_ABI_VERSION. */
size_t srmech_dense_solve_arena_bytes(uint32_t n, uint32_t nrhs)
{
    size_t w = (size_t)n + (size_t)nrhs;
    assert(w >= (size_t)n);                                    /* w = n + nrhs >= n */
    assert(n == 0u || w <= SIZE_MAX / (size_t)n);              /* n*w no overflow */
    return (size_t)n * w * sizeof(double) + sizeof(double);
}

srmech_status_t srmech_dense_solve_f64_ws(uint32_t      n,
                                          uint32_t      nrhs,
                                          const double *A,
                                          const double *B,
                                          double       *out_X,
                                          void         *ws,
                                          size_t        ws_len)
{
    assert(A != NULL);
    assert(B != NULL);
    assert(out_X != NULL);
    if (A == NULL || B == NULL || out_X == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0 || nrhs == 0) {
        return SRMECH_OK;                       /* nothing to solve; ws unused */
    }
    assert(ws != NULL);
    if (ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Carve the augmented [A | B] working matrix from the caller arena `ws`
     * — NO compiled-in size cap: the only bound is ws_len (the caller's RAM).
     * The base is rounded up to an 8-byte boundary for aligned double access
     * (an MCU caller may hand us a byte buffer); the +sizeof(double) slop in
     * srmech_dense_solve_arena_bytes covers that fixup. Rule-3-clean: no malloc. */
    size_t need = srmech_dense_solve_arena_bytes(n, nrhs);
    if (ws_len < need) {
        return SRMECH_ERR_OVERFLOW;             /* caller arena too small */
    }
    uintptr_t aligned = ((uintptr_t)ws + (sizeof(double) - 1u))
                        & ~(uintptr_t)(sizeof(double) - 1u);
    double *aug = (double *)aligned;
    size_t w = (size_t)n + (size_t)nrhs;
    dense_solve_load_aug(n, nrhs, A, B, aug);
    for (uint32_t col = 0; col < n; col++) {
        double mag = dense_solve_pivot(n, nrhs, aug, col);
        if (mag == 0.0) {
            return SRMECH_ERR_BAD_INPUT;
        }
        dense_solve_eliminate(n, nrhs, aug, col);
    }
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = 0; c < nrhs; c++) {
            out_X[(size_t)r * nrhs + c] = aug[(size_t)r * w + (size_t)n + c];
        }
    }
    return SRMECH_OK;
}
