/*
 * srmech_responsion.c — RESPONSION: the response-function family of a
 * generator L acting on an excitation u0 (0.9.0rc208; F1186 — the
 * op(x)operand(x)responsion k=3 completion: the stored relationship itself,
 * the answering-correspondence between successive op-on-operand
 * applications; srmech = Stored-RELATIONSHIP Mechanism).
 *
 * The family has TWO canonical continuous-form members, LAPLACE-TRANSFORM
 * DUALS of one another (the tight, framework-honest member set — not a
 * grab-bag):
 *
 *   kind == 0 (PROPAGATOR, time domain):  e^{-zL}·u0
 *     — a pure DELEGATION to the shipped srmech_eph_propagate cascade
 *       (rc136): same complex-z convention, same arg(z) coherence dial,
 *       same mandatory 2-pi seam-fold, same arena carve (pass-through).
 *
 *   kind == 1 (RESOLVENT, frequency/energy domain — the Green's
 *              function):  (zI - L)^{-1}·u0
 *     — the Laplace transform of the (semigroup) propagator:
 *       (zI - L)^{-1} = integral_0^inf e^{-zt}·e^{tL} dt for
 *       Re(z) > max Re(lambda(L)); per eigenmode the dual pair is
 *       e^{-z·lambda}  <->  1/(z - lambda). Realised as the REAL 2n x 2n
 *       block embedding of the complex system A = zI - L:
 *
 *         [ Ar  -Ai ] [ u ]   [ br ]
 *         [ Ai   Ar ] [ v ] = [ bi ]     =>  x = u + i·v
 *
 *       over the shipped srmech_dense_solve_f64_ws Gauss-Jordan kernel —
 *       the SAME embedding the Python mat_solve complex path rides, so
 *       this is a COMPOSITION of existing C, not a forked solve.
 *
 * A singular A (z EXACTLY in the spectrum of L — a resolvent POLE) returns
 * SRMECH_ERR_BAD_INPUT: the honest pole signal, never a garbage number.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by n
 *   - Rule 3 (no malloc)      : OK — all scratch bump-carved from the
 *                               CALLER arena `ws`
 *   - Rule 4 (≤60 lines/func) : OK — block-build / resolvent / dispatch
 *                               split
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 8 (no multi-line macros) : OK — none defined
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic / /W4
 *
 * No abs()/fabs(): the only magnitude logic lives inside the composed
 * srmech_dense_solve_f64_ws pivot (already a Class-K sign branch).
 * ABI: new symbols only — SRMECH_ABI_VERSION stays 4.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Guard bound so every kind==1 size product below stays far inside
 * size_t: 4·n² doubles must not overflow. 2^24 nodes ≈ a 2 PB block —
 * unreachable RAM long before the arithmetic bound bites. */
#define SRMECH_RESPONSION_MAX_N (1u << 24)

/* Build the REAL 2n x 2n block embedding of A = zI - L into `blk`
 * (row-major, stride 2n): blk = [[Ar, -Ai], [Ai, Ar]] with
 * Ar = Re(z)·I - Re(L), Ai = Im(z)·I - Im(L). is_complex == 0 reads L
 * as n*n real (Im(L) = 0); is_complex != 0 reads L as n*n interleaved
 * (re, im). The subtraction z - L is Class-C signed arithmetic. */
static void responsion_build_block(uint32_t n, int is_complex,
                                   const double *L,
                                   double z_re, double z_im,
                                   double *blk)
{
    assert(L != NULL);
    assert(blk != NULL);
    size_t two_n = 2u * (size_t)n;
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            size_t off = (size_t)i * n + j;
            double l_re = (is_complex != 0) ? L[2u * off] : L[off];
            double l_im = (is_complex != 0) ? L[2u * off + 1u] : 0.0;
            double a_re = ((i == j) ? z_re : 0.0) - l_re;
            double a_im = ((i == j) ? z_im : 0.0) - l_im;
            blk[(size_t)i * two_n + j] = a_re;
            blk[(size_t)i * two_n + (size_t)n + j] = -a_im;
            blk[((size_t)i + n) * two_n + j] = a_im;
            blk[((size_t)i + n) * two_n + (size_t)n + j] = a_re;
        }
    }
}

/* kind == 1: response = (zI - L)^{-1}·u0 via the real 2n x 2n block
 * embedding over srmech_dense_solve_f64_ws. Carves blk (4n² doubles) +
 * rhs (2n) + sol (2n) from the head of `ws` and hands the tail to the
 * inner solve as its arena. A singular block (z in spec(L) — the
 * resolvent pole) surfaces as the solve's SRMECH_ERR_BAD_INPUT. */
static srmech_status_t responsion_resolvent(uint32_t n, int is_complex,
                                            const double *L,
                                            const double *u0,
                                            double z_re, double z_im,
                                            double *out, double *ws,
                                            size_t ws_len)
{
    assert(L != NULL);
    assert(u0 != NULL);
    assert(out != NULL);
    assert(ws != NULL);
    size_t need = srmech_responsion_arena_bytes(n, is_complex, 1);
    if (need == 0u || ws_len < need) {
        return SRMECH_ERR_OVERFLOW;             /* caller arena too small */
    }
    size_t blk_d = 4u * (size_t)n * (size_t)n;  /* (2n)·(2n) block */
    double *blk = ws;
    double *rhs = blk + blk_d;                  /* stacked [b_re; b_im] */
    double *sol = rhs + 2u * (size_t)n;         /* stacked [u; v] */
    double *inner = sol + 2u * (size_t)n;       /* inner solve arena */
    size_t head_bytes = (blk_d + 4u * (size_t)n) * sizeof(double);
    size_t inner_len = ws_len - head_bytes;
    responsion_build_block(n, is_complex, L, z_re, z_im, blk);
    for (uint32_t i = 0; i < n; i++) {
        rhs[i] = u0[2u * (size_t)i];            /* b_re */
        rhs[(size_t)i + n] = u0[2u * (size_t)i + 1u];  /* b_im */
    }
    srmech_status_t st = srmech_dense_solve_f64_ws(
        2u * n, 1u, blk, rhs, sol, (void *)inner, inner_len);
    if (st != SRMECH_OK) {
        return st;      /* BAD_INPUT = the resolvent pole; OVERFLOW = arena */
    }
    for (uint32_t i = 0; i < n; i++) {
        out[2u * (size_t)i] = sol[i];                  /* Re(x_i) = u_i */
        out[2u * (size_t)i + 1u] = sol[(size_t)i + n]; /* Im(x_i) = v_i */
    }
    return SRMECH_OK;
}

/* The caller arena size IN BYTES srmech_responsion needs for an n*n L
 * and the given kind. kind == 0 is the srmech_eph_propagate carve
 * verbatim (pure pass-through delegation); kind == 1 is the 2n x 2n
 * block (4n² doubles) + stacked rhs/sol (4n doubles) + the inner
 * srmech_dense_solve_arena_bytes(2n, 1) arena. Unknown kind -> 0.
 * Adding this symbol does NOT bump SRMECH_ABI_VERSION. */
size_t srmech_responsion_arena_bytes(uint32_t n, int is_complex, int kind)
{
    assert(kind == 0 || kind == 1);
    assert(n <= SRMECH_RESPONSION_MAX_N || kind != 1);
    if (kind == 0) {
        return srmech_eph_propagate_arena_bytes(n, is_complex);
    }
    if (kind != 1 || n > SRMECH_RESPONSION_MAX_N) {
        return 0u;                     /* unknown kind / unreachable size */
    }
    size_t blk_d = 4u * (size_t)n * (size_t)n;      /* n <= 2^24: no wrap */
    size_t head = (blk_d + 4u * (size_t)n) * sizeof(double);
    return head + srmech_dense_solve_arena_bytes(2u * n, 1u);
}

srmech_status_t srmech_responsion(uint32_t      n,
                                  int           is_complex,
                                  int           kind,
                                  const double *L,
                                  const double *u0_interleaved,
                                  double        z_re,
                                  double        z_im,
                                  double       *out_response_interleaved,
                                  double       *ws,
                                  size_t        ws_len)
{
    assert(kind == 0 || kind == 1);
    assert(n == 0u || L != NULL);
    if (kind != 0 && kind != 1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n > SRMECH_RESPONSION_MAX_N) {
        return SRMECH_ERR_BAD_INPUT;   /* size guard (kind-1 block bound) */
    }
    if (L == NULL || u0_interleaved == NULL
            || out_response_interleaved == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) {
        return SRMECH_OK;                    /* nothing to respond to */
    }
    if (ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (kind == 0) {
        /* PROPAGATOR — pure delegation to the shipped EPH cascade. */
        return srmech_eph_propagate(n, is_complex, L, u0_interleaved,
                                    z_re, z_im,
                                    out_response_interleaved, ws, ws_len);
    }
    /* RESOLVENT — the Laplace-dual member. */
    return responsion_resolvent(n, is_complex, L, u0_interleaved,
                                z_re, z_im,
                                out_response_interleaved, ws, ws_len);
}
