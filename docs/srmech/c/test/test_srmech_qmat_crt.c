/*
 * test_srmech_qmat_crt.c -- standalone C smoke for srmech_qmat_rref_crt (the rc48
 * CLOSER of the CRT-QMat re-fibration arc). Proves a C-ONLY host (no Python)
 * computes the exact-Q RREF via the single CRT symbol, byte-identical to what
 * srmech.amsc.qmat.QMat.rref_crt computes -- over a caller-arena sized from
 * srmech_qmat_rref_crt_ws_bound (the answer-Hadamard good-prime budget, NOT the
 * dense Hadamard envelope).
 *
 * Build (from docs/srmech), one line:
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_qmat_crt.c c/src/[star].c -lm -o /tmp/qcrt_smoke
 *
 * Exit 0 on all-pass; aborts (assert) on any mismatch.
 */

#include "srmech.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LCAP 512u

/* Runtime check that SURVIVES -DNDEBUG (Release): assert() would strip both the
 * comparison AND any side-effecting call wrapped in it, so verification + the
 * library calls must run unconditionally. Mirrors the expect_q abort pattern. */
#define CHECK(cond, msg) \
    do { if (!(cond)) { fprintf(stderr, "FAIL %s\n", (msg)); abort(); } } while (0)

typedef struct { uint32_t limbs[LCAP]; srmech_bigint_t bi; } hbi_t;

static void hbi_set(hbi_t *h, const char *dec)
{
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
    CHECK(srmech_bigint_from_dec(&h->bi, dec, strlen(dec)) == SRMECH_OK,
          "bigint_from_dec");
}

static void hbi_blank(hbi_t *h)
{
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
}

static void hbi_dec(const srmech_bigint_t *a, char *buf, size_t cap)
{
    static uint32_t ws[LCAP * 16];
    size_t outlen = 0u;
    CHECK(srmech_bigint_to_dec(a, buf, cap, &outlen, ws, sizeof(ws)) == SRMECH_OK,
          "bigint_to_dec");
}

static void expect_q(const srmech_bigint_t *num, const srmech_bigint_t *den,
                     const char *en, const char *ed, const char *what)
{
    char bn[16384], bd[16384];
    hbi_dec(num, bn, sizeof(bn));
    hbi_dec(den, bd, sizeof(bd));
    if (strcmp(bn, en) != 0 || strcmp(bd, ed) != 0) {
        fprintf(stderr, "FAIL %s: got %s/%s expected %s/%s\n", what, bn, bd, en, ed);
        abort();
    }
}

#define MAXCELLS 64u

typedef struct {
    hbi_t num[MAXCELLS];
    hbi_t den[MAXCELLS];
    srmech_bigint_t bn[MAXCELLS];
    srmech_bigint_t bd[MAXCELLS];
    size_t rows, cols;
} hmat_t;

static void hmat_set(hmat_t *m, const char *const *nums, const char *const *dens,
                     size_t rows, size_t cols)
{
    size_t i, cells = rows * cols;
    assert(cells <= MAXCELLS);
    m->rows = rows; m->cols = cols;
    for (i = 0u; i < cells; i++) {
        hbi_set(&m->num[i], nums[i]);
        hbi_set(&m->den[i], dens[i]);
        m->bn[i] = m->num[i].bi;
        m->bd[i] = m->den[i].bi;
    }
}

static void hmat_blank(hmat_t *m, size_t cells)
{
    size_t i;
    assert(cells <= MAXCELLS);
    for (i = 0u; i < cells; i++) {
        hbi_blank(&m->num[i]);
        hbi_blank(&m->den[i]);
        m->bn[i] = m->num[i].bi;
        m->bd[i] = m->den[i].bi;
    }
}

static void hmat_sync(hmat_t *m, size_t cells)
{
    size_t i;
    for (i = 0u; i < cells; i++) {
        m->num[i].bi = m->bn[i];
        m->den[i].bi = m->bd[i];
    }
}

static uint32_t *g_arena = NULL;
static size_t g_arena_words = 0u;

static void arena_ensure(size_t bytes)
{
    size_t words = bytes / sizeof(uint32_t) + 8u;
    if (words > g_arena_words) {
        free(g_arena);
        g_arena = (uint32_t *)malloc(words * sizeof(uint32_t));
        assert(g_arena != NULL);
        g_arena_words = words;
    }
}

static int npass = 0;

/* Run rref_crt into the harness output, sizing the arena from the ws-bound. */
static size_t run_crt(hmat_t *a, hmat_t *o, size_t r, size_t c, size_t *piv)
{
    size_t rank = 0u, ws = srmech_qmat_rref_crt_ws_bound(8u, r, c);
    arena_ensure(ws);
    hmat_blank(o, r * c);
    CHECK(srmech_qmat_rref_crt(a->bn, a->bd, r, c, o->bn, o->bd, &rank, piv,
                               g_arena, ws) == SRMECH_OK, "qmat_rref_crt");
    hmat_sync(o, r * c);
    return rank;
}

/* full-rank 3x3 integer -> identity */
static void t_crt_identity(void)
{
    const char *n[] = {"1","2","3","4","5","6","7","8","10"};
    const char *d[] = {"1","1","1","1","1","1","1","1","1"};
    hmat_t a, o; size_t piv[8], rank;
    hmat_set(&a, n, d, 3, 3);
    rank = run_crt(&a, &o, 3, 3, piv);
    CHECK(rank == 3, "rank == 3");
    expect_q(&o.bn[0], &o.bd[0], "1", "1", "crt-id[0,0]");
    expect_q(&o.bn[4], &o.bd[4], "1", "1", "crt-id[1,1]");
    expect_q(&o.bn[8], &o.bd[8], "1", "1", "crt-id[2,2]");
    expect_q(&o.bn[1], &o.bd[1], "0", "1", "crt-id[0,1]");
    npass++;
}

/* 2x3 with a free column carrying fractional rationals (the residue-sign case):
 * [[1,2,3],[2,4,7]] -> [[1,2,0],[0,0,1]] (col 1 is free, col 2 the second pivot).
 * Verifies the free-column entries reconstruct exactly. */
static void t_crt_free_column(void)
{
    const char *n[] = {"1","2","3","2","4","7"};
    const char *d[] = {"1","1","1","1","1","1"};
    hmat_t a, o; size_t piv[8], rank;
    hmat_set(&a, n, d, 2, 3);
    rank = run_crt(&a, &o, 2, 3, piv);
    CHECK(rank == 2, "rank == 2");
    expect_q(&o.bn[0], &o.bd[0], "1", "1", "crt-free[0,0]");
    expect_q(&o.bn[1], &o.bd[1], "2", "1", "crt-free[0,1]");
    expect_q(&o.bn[2], &o.bd[2], "0", "1", "crt-free[0,2]");
    expect_q(&o.bn[5], &o.bd[5], "1", "1", "crt-free[1,2]");
    npass++;
}

/* fractional inputs with negative numerator (the FLOOR-residue path):
 * [[1/2, -1/3],[1/5, 1/7]] is full rank -> identity. */
static void t_crt_fractional_negative(void)
{
    const char *n[] = {"1","-1","1","1"};
    const char *d[] = {"2","3","5","7"};
    hmat_t a, o; size_t piv[8], rank;
    hmat_set(&a, n, d, 2, 2);
    rank = run_crt(&a, &o, 2, 2, piv);
    CHECK(rank == 2, "rank == 2");
    expect_q(&o.bn[0], &o.bd[0], "1", "1", "crt-frac[0,0]");
    expect_q(&o.bn[1], &o.bd[1], "0", "1", "crt-frac[0,1]");
    expect_q(&o.bn[3], &o.bd[3], "1", "1", "crt-frac[1,1]");
    npass++;
}

/* first-prime-unlucky consensus-restart: det == 2147483647 (the first descending
 * GF prime) so the matrix drops rank mod that prime -> the consensus must restart
 * on a later lucky prime; the exact RREF is still recovered (identity). */
static void t_crt_unlucky_restart(void)
{
    const char *n[] = {"2147483647","1","0","1"};
    const char *d[] = {"1","1","1","1"};
    hmat_t a, o; size_t piv[8], rank;
    hmat_set(&a, n, d, 2, 2);
    rank = run_crt(&a, &o, 2, 2, piv);
    CHECK(rank == 2, "rank == 2");
    expect_q(&o.bn[0], &o.bd[0], "1", "1", "crt-unlucky[0,0]");
    expect_q(&o.bn[1], &o.bd[1], "0", "1", "crt-unlucky[0,1]");
    expect_q(&o.bn[3], &o.bd[3], "1", "1", "crt-unlucky[1,1]");
    npass++;
}

/* big-magnitude free-column answer (num/den > 2**64): an augmented [A|b] shape
 * carries the bigint rational into the trailing column. A = [[2,1],[1,3]] (det 5),
 * b = [[10^40+1],[1]] -> the unique x reconstructs exactly as a bigint rational. */
static void t_crt_big_answer(void)
{
    /* [A | b]: rows [2,1,(10^40+1)] and [1,3,1]. RREF -> [[1,0,x0],[0,1,x1]]. */
    const char *n[] = {"2","1","10000000000000000000000000000000000000001",
                       "1","3","1"};
    const char *d[] = {"1","1","1","1","1","1"};
    hmat_t a, o; size_t piv[8], rank;
    char bn[16384];
    hmat_set(&a, n, d, 2, 3);
    rank = run_crt(&a, &o, 2, 3, piv);
    CHECK(rank == 2, "rank == 2");
    expect_q(&o.bn[0], &o.bd[0], "1", "1", "crt-big[0,0]");
    expect_q(&o.bn[4], &o.bd[4], "1", "1", "crt-big[1,1]");
    /* x0 = (3*b0 - b1)/5 = (3*(10^40+1) - 1)/5 = (3*10^40+2)/5, already reduced
     * (denominator 5). Confirm the numerator exceeds 2**64 (a genuine bigint
     * reconstruction) and matches exactly. */
    hbi_dec(&o.bn[2], bn, sizeof(bn));
    assert(strlen(bn) > 19);                /* > 2**64 has >= 20 decimal digits */
    expect_q(&o.bn[2], &o.bd[2],
             "30000000000000000000000000000000000000002", "5", "crt-big x0");
    expect_q(&o.bn[5], &o.bd[5],
             "-9999999999999999999999999999999999999999", "5", "crt-big x1");
    npass++;
}

int main(void)
{
    t_crt_identity();
    t_crt_free_column();
    t_crt_fractional_negative();
    t_crt_unlucky_restart();
    t_crt_big_answer();
    free(g_arena);
    printf("srmech_qmat_crt smoke: %d/%d cases pass\n", npass, npass);
    return 0;
}
