/*
 * test_srmech_hdc.c — C smoke for the §50 native Klein-4 co-occurrence fold
 * (srmech_klein4_cooccurrence_fold, UPSTREAM §50; rc165).
 *
 * The fold's accumulators are hand-computed for a tiny 5-token / 3-code corpus
 * (window 1) so the C kernel is checked directly (not only via Python parity).
 * Tokens (by code index): [0, 1, 2, 1, 0]; codes (dim 4):
 *   code0 = {0,1,2,3}   code1 = {1,1,1,1}   code2 = {2,2,2,2}
 * Neighbour folds (±1, excluding self):
 *   pos0(c0)->{c1} · pos1(c1)->{c0,c2} · pos2(c2)->{c1,c1} ·
 *   pos3(c1)->{c2,c0} · pos4(c0)->{c1}
 * so per token: acc[c0]=2*c1 (n=2); acc[c1]=2*c0+2*c2 (n=4); acc[c2]=2*c1 (n=2).
 * Accumulator layout: [n, bit0-1counts[dim], bit1-1counts[dim]] (stride 1+2*dim).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *msg)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", msg); }
    else      { g_fail++; printf("  FAIL  %s\n", msg); }
}

#define DIM 4u
#define STRIDE (1u + 2u * DIM)        /* = 9 */

static int acc_eq(const uint32_t *acc, const uint32_t *expect)
{
    for (uint32_t k = 0; k < STRIDE; k++) {
        if (acc[k] != expect[k]) { return 0; }
    }
    return 1;
}

int main(void)
{
    printf("== srmech_hdc smoke tests (rc165 §50 native co-occurrence fold) ==\n");

    /* 3 codes (dim 4), row-major: codes[ci*DIM + j] */
    uint8_t codes[3u * DIM] = {
        0u, 1u, 2u, 3u,   /* code0 */
        1u, 1u, 1u, 1u,   /* code1 */
        2u, 2u, 2u, 2u,   /* code2 */
    };
    uint32_t tok_idx[5] = { 0u, 1u, 2u, 1u, 0u };
    uint32_t out_accs[3u * STRIDE];

    srmech_status_t st = srmech_klein4_cooccurrence_fold(
        codes, 3u, tok_idx, 5u, 1u, DIM, out_accs);
    check(st == SRMECH_OK, "fold returns SRMECH_OK");

    /* expected accumulators (see header hand-computation) */
    uint32_t e0[STRIDE] = { 2u, 2u,2u,2u,2u, 0u,0u,0u,0u };   /* 2*code1 */
    uint32_t e1[STRIDE] = { 4u, 0u,2u,0u,2u, 2u,2u,4u,4u };   /* 2*code0+2*code2 */
    uint32_t e2[STRIDE] = { 2u, 2u,2u,2u,2u, 0u,0u,0u,0u };   /* 2*code1 */
    check(acc_eq(&out_accs[0u * STRIDE], e0), "code0 accumulator == 2*code1 (n=2)");
    check(acc_eq(&out_accs[1u * STRIDE], e1),
          "code1 accumulator == 2*code0 + 2*code2 (n=4)");
    check(acc_eq(&out_accs[2u * STRIDE], e2), "code2 accumulator == 2*code1 (n=2)");

    /* resolving code1's accumulator: strict majority over n=4 (half=2) */
    uint8_t bundle1[DIM];
    st = srmech_klein4_bundle_resolve(&out_accs[1u * STRIDE], bundle1, DIM);
    uint8_t exp1[DIM] = { 0u, 0u, 2u, 2u };   /* b1 set where 1count>2; b0 none */
    check(st == SRMECH_OK && memcmp(bundle1, exp1, DIM) == 0,
          "resolve(code1 acc) == {0,0,2,2}");

    /* resolving code0's accumulator (only co-occurs with code1) -> code1 */
    uint8_t bundle0[DIM];
    st = srmech_klein4_bundle_resolve(&out_accs[0u * STRIDE], bundle0, DIM);
    uint8_t exp0[DIM] = { 1u, 1u, 1u, 1u };   /* == code1 */
    check(st == SRMECH_OK && memcmp(bundle0, exp0, DIM) == 0,
          "resolve(code0 acc) == code1 {1,1,1,1}");

    /* a bad code byte (> 3) is rejected */
    uint8_t bad_codes[DIM] = { 0u, 4u, 0u, 0u };   /* 4 is out of {0..3} */
    uint32_t bad_tok[2] = { 0u, 0u };
    uint32_t bad_out[1u * STRIDE];
    st = srmech_klein4_cooccurrence_fold(bad_codes, 1u, bad_tok, 2u, 1u, DIM, bad_out);
    check(st == SRMECH_ERR_BAD_INPUT, "out-of-range code byte -> BAD_INPUT");

    /* an out-of-range token index is rejected */
    uint32_t oob_tok[2] = { 0u, 7u };   /* 7 >= n_codes(1) */
    st = srmech_klein4_cooccurrence_fold(codes, 1u, oob_tok, 2u, 1u, DIM, bad_out);
    check(st == SRMECH_ERR_BAD_INPUT, "out-of-range token index -> BAD_INPUT");

    printf("== %d passed, %d failed ==\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
