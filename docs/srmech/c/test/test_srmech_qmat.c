/*
 * test_srmech_qmat.c — standalone C smoke for the exact-rational matrix carrier
 * srmech_qmat_* (the C peer of srmech.amsc.qmat.QMat; the §76 gosper exact-ℚ
 * solve foundation). Proves the C-only host computes the same exact-Q entries the
 * Python QMat does — rref / rank / det / inverse / solve / nullspace — over
 * caller-arena srmech_bigint, with NO Python present.
 *
 * Build (from docs/srmech), one line:
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_qmat.c c/src/[star].c -lm -o /tmp/qmat_smoke
 *
 * Exit 0 on all-pass; aborts (assert) on any mismatch.
 */

#include "srmech.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LCAP 512u    /* limbs per harness bigint — far past the 81-digit det (~9 limbs) */

typedef struct { uint32_t limbs[LCAP]; srmech_bigint_t bi; } hbi_t;

static void hbi_set(hbi_t *h, const char *dec)
{
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
    assert(srmech_bigint_from_dec(&h->bi, dec, strlen(dec)) == SRMECH_OK);
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
    assert(srmech_bigint_to_dec(a, buf, cap, &outlen, ws, sizeof(ws)) == SRMECH_OK);
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

/* ---- a fixed-width matrix harness (row-major srmech_bigint arrays) ---- */

#define MAXCELLS 36u

typedef struct {
    hbi_t num[MAXCELLS];
    hbi_t den[MAXCELLS];
    srmech_bigint_t bn[MAXCELLS];
    srmech_bigint_t bd[MAXCELLS];
    size_t rows, cols;
} hmat_t;

/* Build from parallel decimal num/den string arrays (row-major). */
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

/* ---- rref ---- */
static void t_rref(void)
{
    /* [[1,2,3],[4,5,6],[7,8,10]] (full rank 3) -> identity */
    const char *n[] = {"1","2","3","4","5","6","7","8","10"};
    const char *d[] = {"1","1","1","1","1","1","1","1","1"};
    hmat_t a, o; size_t rank = 0u, piv[8], ws;
    hmat_set(&a, n, d, 3, 3);
    hmat_blank(&o, 9);
    ws = srmech_qmat_ws_bound(2u, 3u, 3u); arena_ensure(ws);
    assert(srmech_qmat_rref(a.bn, a.bd, 3, 3, o.bn, o.bd, &rank, piv,
                            g_arena, ws) == SRMECH_OK);
    hmat_sync(&o, 9);
    assert(rank == 3);
    expect_q(&o.bn[0], &o.bd[0], "1", "1", "rref[0,0]");
    expect_q(&o.bn[1], &o.bd[1], "0", "1", "rref[0,1]");
    expect_q(&o.bn[4], &o.bd[4], "1", "1", "rref[1,1]");
    expect_q(&o.bn[8], &o.bd[8], "1", "1", "rref[2,2]");
    npass++;
}

/* ---- det (full + singular + the 81-digit keystone) ---- */
static void t_det_small(void)
{
    /* det [[1,2],[3,4]] = -2 */
    const char *n[] = {"1","2","3","4"}, *d[] = {"1","1","1","1"};
    hmat_t a; hbi_t on, od; size_t ws;
    srmech_bigint_t bn, bd;
    hmat_set(&a, n, d, 2, 2);
    hbi_blank(&on); hbi_blank(&od); bn = on.bi; bd = od.bi;
    ws = srmech_qmat_ws_bound(2u, 2u, 4u); arena_ensure(ws);
    assert(srmech_qmat_det(a.bn, a.bd, 2, &bn, &bd, g_arena, ws) == SRMECH_OK);
    on.bi = bn; od.bi = bd;
    expect_q(&on.bi, &od.bi, "-2", "1", "det 2x2");
    npass++;
}

static void t_det_singular(void)
{
    /* det [[1,2],[2,4]] = 0 */
    const char *n[] = {"1","2","2","4"}, *d[] = {"1","1","1","1"};
    hmat_t a; hbi_t on, od; size_t ws;
    srmech_bigint_t bn, bd;
    hmat_set(&a, n, d, 2, 2);
    hbi_blank(&on); hbi_blank(&od); bn = on.bi; bd = od.bi;
    ws = srmech_qmat_ws_bound(2u, 2u, 4u); arena_ensure(ws);
    assert(srmech_qmat_det(a.bn, a.bd, 2, &bn, &bd, g_arena, ws) == SRMECH_OK);
    on.bi = bn; od.bi = bd;
    expect_q(&on.bi, &od.bi, "0", "1", "det singular");
    npass++;
}

static void t_det_keystone(void)
{
    /* 2x2 with Q(10^40+1, 3^30) on the diagonal, 1 off — det should be
     * (10^40+1)^2 / 3^60 - 1, a big-num exact rational (no ceiling). The exact
     * expected value is computed by the harness from decimal strings below.
     *   a = (10^40+1)/3^30, det = a*a - 1*1 = (a^2*3^60 - 3^60)/3^60.
     * 3^30 = 205891132094649; 3^60 = 42391158275216203514294433201.
     * (10^40+1)^2 = 10^80 + 2*10^40 + 1.
     *   num = (10^80 + 2*10^40 + 1) - 3^60
     *       = 100...(81 digits) - 42391158275216203514294433201
     *   den = 3^60 = 42391158275216203514294433201            */
    const char *n[] = {
        "10000000000000000000000000000000000000001", "1",
        "1", "10000000000000000000000000000000000000001"};
    const char *d[] = {"205891132094649","1","1","205891132094649"};
    /* expected num/den from the fractions.Fraction oracle (81-digit numerator) */
    const char *exp_num =
        "1000000000000000000000000000000000000000"
        "19999999999957608841724783796485705566800";
    const char *exp_den = "42391158275216203514294433201";
    hmat_t a; hbi_t on, od; size_t ws;
    srmech_bigint_t bn, bd;
    hmat_set(&a, n, d, 2, 2);
    hbi_blank(&on); hbi_blank(&od); bn = on.bi; bd = od.bi;
    ws = srmech_qmat_ws_bound(8u, 2u, 4u); arena_ensure(ws);
    assert(srmech_qmat_det(a.bn, a.bd, 2, &bn, &bd, g_arena, ws) == SRMECH_OK);
    on.bi = bn; od.bi = bd;
    expect_q(&on.bi, &od.bi, exp_num, exp_den, "det keystone 81-digit");
    npass++;
}

/* ---- inverse ---- */
static void t_inverse(void)
{
    /* inv [[4,7],[2,6]] = [[0.6,-0.7],[-0.2,0.4]] = [[3/5,-7/10],[-1/5,2/5]] */
    const char *n[] = {"4","7","2","6"}, *d[] = {"1","1","1","1"};
    hmat_t a, o; int sing = 0; size_t ws;
    hmat_set(&a, n, d, 2, 2);
    hmat_blank(&o, 4);
    ws = srmech_qmat_ws_bound(2u, 2u, 4u); arena_ensure(ws);
    assert(srmech_qmat_inverse(a.bn, a.bd, 2, o.bn, o.bd, &sing,
                               g_arena, ws) == SRMECH_OK);
    hmat_sync(&o, 4);
    assert(sing == 0);
    expect_q(&o.bn[0], &o.bd[0], "3", "5", "inv[0,0]");
    expect_q(&o.bn[1], &o.bd[1], "-7", "10", "inv[0,1]");
    expect_q(&o.bn[2], &o.bd[2], "-1", "5", "inv[1,0]");
    expect_q(&o.bn[3], &o.bd[3], "2", "5", "inv[1,1]");
    npass++;
}

static void t_inverse_singular(void)
{
    const char *n[] = {"1","2","2","4"}, *d[] = {"1","1","1","1"};
    hmat_t a, o; int sing = 0; size_t ws;
    hmat_set(&a, n, d, 2, 2);
    hmat_blank(&o, 4);
    ws = srmech_qmat_ws_bound(2u, 2u, 4u); arena_ensure(ws);
    assert(srmech_qmat_inverse(a.bn, a.bd, 2, o.bn, o.bd, &sing,
                               g_arena, ws) == SRMECH_OK);
    assert(sing == 1);
    npass++;
}

/* ---- solve ---- */
static void t_solve(void)
{
    /* [[2,1],[1,3]] x = [3;5] -> x = [4/5; 7/5] */
    const char *n[] = {"2","1","1","3"}, *d[] = {"1","1","1","1"};
    const char *bn[] = {"3","5"}, *bd[] = {"1","1"};
    hmat_t a, b, o; int sing = 0; size_t ws;
    hmat_set(&a, n, d, 2, 2);
    hmat_set(&b, bn, bd, 2, 1);
    hmat_blank(&o, 2);
    ws = srmech_qmat_ws_bound(2u, 2u, 3u); arena_ensure(ws);
    assert(srmech_qmat_solve(a.bn, a.bd, 2, b.bn, b.bd, 1, o.bn, o.bd, &sing,
                             g_arena, ws) == SRMECH_OK);
    hmat_sync(&o, 2);
    assert(sing == 0);
    expect_q(&o.bn[0], &o.bd[0], "4", "5", "solve x0");
    expect_q(&o.bn[1], &o.bd[1], "7", "5", "solve x1");
    npass++;
}

static void t_solve_singular(void)
{
    const char *n[] = {"1","2","2","4"}, *d[] = {"1","1","1","1"};
    const char *bn[] = {"1","2"}, *bd[] = {"1","1"};
    hmat_t a, b, o; int sing = 0; size_t ws;
    hmat_set(&a, n, d, 2, 2);
    hmat_set(&b, bn, bd, 2, 1);
    hmat_blank(&o, 2);
    ws = srmech_qmat_ws_bound(2u, 2u, 3u); arena_ensure(ws);
    assert(srmech_qmat_solve(a.bn, a.bd, 2, b.bn, b.bd, 1, o.bn, o.bd, &sing,
                             g_arena, ws) == SRMECH_OK);
    assert(sing == 1);
    npass++;
}

/* ---- nullspace ---- */
static void t_nullspace(void)
{
    /* A = [[1,2,3],[2,4,6]] (rank 1). RREF = [[1,2,3],[0,0,0]]. Free cols 1,2.
     * QMat basis: for fc=1: v=[-2,1,0]; for fc=2: v=[-3,0,1]. Stored column-major:
     * out[i*ncols + j]. ncols=3, nfree=2. */
    const char *n[] = {"1","2","3","2","4","6"};
    const char *d[] = {"1","1","1","1","1","1"};
    hmat_t a, o; size_t nfree = 0u, ws;
    hmat_set(&a, n, d, 2, 3);
    hmat_blank(&o, 9);
    ws = srmech_qmat_ws_bound(2u, 2u, 3u); arena_ensure(ws);
    assert(srmech_qmat_nullspace(a.bn, a.bd, 2, 3, o.bn, o.bd, &nfree,
                                 g_arena, ws) == SRMECH_OK);
    hmat_sync(&o, 9);
    assert(nfree == 2);
    /* basis col 0 = [-2,1,0]: out[0*3+0], out[1*3+0], out[2*3+0] */
    expect_q(&o.bn[0], &o.bd[0], "-2", "1", "null0[0]");
    expect_q(&o.bn[3], &o.bd[3], "1", "1", "null0[1]");
    expect_q(&o.bn[6], &o.bd[6], "0", "1", "null0[2]");
    /* basis col 1 = [-3,0,1]: out[0*3+1], out[1*3+1], out[2*3+1] */
    expect_q(&o.bn[1], &o.bd[1], "-3", "1", "null1[0]");
    expect_q(&o.bn[4], &o.bd[4], "0", "1", "null1[1]");
    expect_q(&o.bn[7], &o.bd[7], "1", "1", "null1[2]");
    npass++;
}

int main(void)
{
    t_rref();
    t_det_small();
    t_det_singular();
    t_det_keystone();
    t_inverse();
    t_inverse_singular();
    t_solve();
    t_solve_singular();
    t_nullspace();
    free(g_arena);
    printf("srmech_qmat smoke: %d/%d cases pass\n", npass, npass);
    return 0;
}
