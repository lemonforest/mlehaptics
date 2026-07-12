/*
 * test_srmech_carrier.c — standalone BARE-C-HOST smoke for the rc141
 * Mat/Vec carrier struct API (Foundation F0). Proves a C host with NO
 * Python present can: size a backing buffer, construct a carrier over it,
 * get/set elements, take row/col views, do elementwise + scalar + unary
 * arithmetic, transpose, and feed the carrier buffer STRAIGHT to the
 * existing compute kernel (srmech_dense_matmul_complex) ZERO-COPY.
 *
 * All buffers are caller-owned static arenas (no malloc — the whole point:
 * a microcontroller host holds carriers with no allocator).
 *
 * Build (WSL / POSIX), Release to match the CI pedantic cell (NDEBUG strips
 * assert(), so an assert-only param would warn -Werror=unused-parameter):
 *   gcc -std=c11 -O2 -DNDEBUG -Wall -Wextra -Wpedantic -Werror -Ic/include \
 *       c/test/test_srmech_carrier.c c/src/srmech_carrier.c \
 *       c/src/srmech_laplacian.c -o /tmp/carrier_smoke
 *   /tmp/carrier_smoke            (exit 0 = all pass)
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>

static int g_pass = 0;
static int g_fail = 0;

#define CHECK(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { g_fail++; printf("  FAIL: %s\n", (msg)); } \
} while (0)

static int close_to(double a, double b)
{
    double d = a - b;
    if (d < 0.0) { d = -d; }
    return d <= 1e-12;
}

/* Static caller arenas (no malloc). Interleaved (re,im) sized generously. */
static double g_a[32];
static double g_b[32];
static double g_out[32];
static double g_vbuf[32];

static void test_real_mat(void)
{
    srmech_mat_t A, B, O;
    double re = 0.0, im = -1.0;
    /* srmech_mat_buf_len(2,3,real) == 6 doubles. */
    CHECK(srmech_mat_buf_len(2u, 3u, 0) == 6u, "mat_buf_len real 2x3");
    CHECK(srmech_mat_buf_len(2u, 3u, 1) == 12u, "mat_buf_len complex 2x3");
    /* Build A = [[1,2,3],[4,5,6]] via zeros + set; read back via get. */
    srmech_mat_zeros(&A, g_a, 2u, 3u, 0);
    srmech_mat_set(&A, 0u, 0u, 1.0, 0.0);
    srmech_mat_set(&A, 0u, 1u, 2.0, 0.0);
    srmech_mat_set(&A, 0u, 2u, 3.0, 0.0);
    srmech_mat_set(&A, 1u, 0u, 4.0, 0.0);
    srmech_mat_set(&A, 1u, 1u, 5.0, 0.0);
    srmech_mat_set(&A, 1u, 2u, 6.0, 0.0);
    srmech_mat_get(&A, 1u, 2u, &re, &im);
    CHECK(close_to(re, 6.0) && close_to(im, 0.0), "real get (1,2)==6");
    /* B = [[10,20,30],[40,50,60]]; O = A + B elementwise. */
    srmech_mat_zeros(&B, g_b, 2u, 3u, 0);
    srmech_mat_scale(&A, 10.0, 0.0, &B);   /* B = 10*A */
    srmech_mat_zeros(&O, g_out, 2u, 3u, 0);
    srmech_mat_add(&A, &B, &O);
    srmech_mat_get(&O, 0u, 0u, &re, NULL);
    CHECK(close_to(re, 11.0), "real (A + 10A)[0,0]==11");
    srmech_mat_get(&O, 1u, 2u, &re, NULL);
    CHECK(close_to(re, 66.0), "real (A + 10A)[1,2]==66");
    /* Row + column views. */
    srmech_vec_t v;
    srmech_vec_init(&v, g_vbuf, 3u, 0);
    srmech_mat_row(&A, 1u, &v);
    srmech_vec_get(&v, 0u, &re, NULL);
    CHECK(close_to(re, 4.0), "row(1)[0]==4");
    srmech_vec_init(&v, g_vbuf, 2u, 0);
    srmech_mat_col(&A, 2u, &v);
    srmech_vec_get(&v, 1u, &re, NULL);
    CHECK(close_to(re, 6.0), "col(2)[1]==6");
}

static void test_complex_mat_and_bridge(void)
{
    srmech_mat_t A, B, O, T;
    double re = 0.0, im = 0.0;
    /* A = [[1+2i, 3+0i],[0+1i, 2-1i]] (interleaved). */
    srmech_mat_zeros(&A, g_a, 2u, 2u, 1);
    srmech_mat_set(&A, 0u, 0u, 1.0, 2.0);
    srmech_mat_set(&A, 0u, 1u, 3.0, 0.0);
    srmech_mat_set(&A, 1u, 0u, 0.0, 1.0);
    srmech_mat_set(&A, 1u, 1u, 2.0, -1.0);
    /* conj(A)[0,0] == 1-2i (Class-K sign flip on imag). */
    srmech_mat_zeros(&B, g_b, 2u, 2u, 1);
    srmech_mat_conj(&A, &B);
    srmech_mat_get(&B, 0u, 0u, &re, &im);
    CHECK(close_to(re, 1.0) && close_to(im, -2.0), "conj[0,0]==1-2i");
    /* transpose(A)[0,1] == A[1,0] == 0+1i. */
    srmech_mat_zeros(&T, g_out, 2u, 2u, 1);
    srmech_mat_transpose(&A, &T);
    srmech_mat_get(&T, 0u, 1u, &re, &im);
    CHECK(close_to(re, 0.0) && close_to(im, 1.0), "transpose[0,1]==0+1i");
    /* Hadamard A*A: [0,0] == (1+2i)^2 == -3+4i. */
    srmech_mat_zeros(&O, g_b, 2u, 2u, 1);
    srmech_mat_mul(&A, &A, &O);
    srmech_mat_get(&O, 0u, 0u, &re, &im);
    CHECK(close_to(re, -3.0) && close_to(im, 4.0), "hadamard[0,0]==-3+4i");
    /* KERNEL BRIDGE: I = identity; A @ I == A (feeds the buffer to
     * srmech_dense_matmul_complex zero-copy). */
    srmech_mat_zeros(&B, g_b, 2u, 2u, 1);
    srmech_mat_set(&B, 0u, 0u, 1.0, 0.0);
    srmech_mat_set(&B, 1u, 1u, 1.0, 0.0);
    srmech_mat_zeros(&O, g_out, 2u, 2u, 1);
    CHECK(srmech_mat_matmul_c128(&A, &B, &O) == SRMECH_OK, "bridge matmul OK");
    srmech_mat_get(&O, 1u, 1u, &re, &im);
    CHECK(close_to(re, 2.0) && close_to(im, -1.0), "(A@I)[1,1]==2-1i");
    srmech_mat_get(&O, 0u, 0u, &re, &im);
    CHECK(close_to(re, 1.0) && close_to(im, 2.0), "(A@I)[0,0]==1+2i");
}

int main(void)
{
    test_real_mat();
    test_complex_mat_and_bridge();
    printf("srmech_carrier smoke: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
