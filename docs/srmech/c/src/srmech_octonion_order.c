/*
 * srmech_octonion_order.c — the octonion ORDER fingerprint (0.9.0rc247, gh
 * #1390 item 4b / F1231). The byte-exact C twin of
 * srmech.amsc.laplacian.order_fingerprint: the path-ORDERED product of a generic
 * octonion per node along a walk, an order-sensitive length-independent
 * fingerprint (8 ints) — the recover_check ORDER faculty that catches a
 * graph-preserving REORDER the op/operand/responsion/ℂ-curvature faculties miss.
 *
 * The octonion structure is NOT hand-rolled here (the F372 trap): the 8×8
 * cocycle is read from the attested, C-mirrored srmech_cd_basis_product
 * (e_i·e_j = sign·e_index), so the C table provably matches the Python
 * octonion_mult_table it is built from.
 *
 * Reduced mod P = 2^31 − 1 after every multiply — a node octonion's components
 * are ≤ 24, so with acc < 2^31 the product acc[i]·no[j] < 2^36 and the 8-term
 * sum < 2^39: no int64 overflow before the reduction, and the fingerprint is
 * bounded (a bignum-free byte-exact peer). No malloc; no abs.
 * ADDITIVE symbol — SRMECH_ABI_VERSION stays 5.
 */
#include "srmech.h"

#include <assert.h>

#define OCT_FP_P ((int64_t)((1u << 31) - 1u))   /* Mersenne prime 2^31 − 1 */

/* A deterministic GENERIC octonion for one node id: real part 1 + seven
 * distinct-per-axis id-derived imaginary parts (byte-exact with the pure
 * _node_octonion). id·(2k+3)+(5k+1) is computed in uint64 (id < 2^32, factor
 * ≤ 15 → < 2^36) so it never overflows before the small modulus. */
static void oct_node(uint32_t id, int64_t out[8])
{
    int k;
    assert(out != NULL);
    out[0] = 1;
    for (k = 0; k < 7; k++) {
        uint64_t v = (uint64_t)id * (uint64_t)(2 * k + 3)
                   + (uint64_t)(5 * k + 1);
        out[k + 1] = (int64_t)(1u + (uint32_t)(v % (uint64_t)(11 + 2 * k)));
    }
}

srmech_status_t srmech_octonion_order_fingerprint(
    const uint32_t *fiber, size_t nf, int64_t out[8])
{
    int idx[8][8];
    int sgn[8][8];
    int64_t acc[8];
    int64_t prod[8];
    int64_t no[8];
    size_t f;
    int i, j, k;
    srmech_status_t st;
    assert(out != NULL);
    assert(fiber != NULL || nf == 0u);
    if (out == NULL || (nf > 0u && fiber == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (i = 0; i < 8; i++) {                    /* the 8×8 CD cocycle */
        for (j = 0; j < 8; j++) {
            st = srmech_cd_basis_product(8, i, j, &idx[i][j], &sgn[i][j]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    acc[0] = 1;
    for (i = 1; i < 8; i++) { acc[i] = 0; }
    for (f = 0; f < nf; f++) {
        oct_node(fiber[f], no);
        for (k = 0; k < 8; k++) { prod[k] = 0; }
        for (i = 0; i < 8; i++) {
            if (acc[i] == 0) { continue; }
            for (j = 0; j < 8; j++) {
                if (no[j] == 0) { continue; }
                prod[idx[i][j]] += (int64_t)sgn[i][j] * acc[i] * no[j];
            }
        }
        for (k = 0; k < 8; k++) {
            int64_t r = prod[k] % OCT_FP_P;       /* → [0, P) matching Python % */
            acc[k] = (r < 0) ? r + OCT_FP_P : r;
        }
    }
    for (k = 0; k < 8; k++) { out[k] = acc[k]; }
    return SRMECH_OK;
}
