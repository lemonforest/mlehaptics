/* test_encoder.c — verify 640-dim encoder against Python reference.
 *
 * Verification hierarchy (for every test position):
 *   1. board_signal() matches reference
 *   2. Each D4 irrep projection matches reference
 *   3. Each symmetric fiber channel matches reference
 *   4. Antisymmetric channel matches reference (dims 512-575)
 *   5. Diagonal channel matches reference (dims 576-639)
 *   6. Full 640-dim encoding matches reference
 *   7. Backward-compat: dims 0..511 of encode_640() == encode_512_spectral()
 */
#include <stdio.h>
#include <math.h>
#include "cs_encoder.h"
#include "test_vectors.h"

/* Tight tolerance for channels the C code reproduces directly from the
 * Python reference (same math, same constants, different language). */
#define TOL_CORE  1e-10
/* Bit-equal tolerance for backward-compat check (same double-precision path). */
#define TOL_BC    1e-10

static double absdiff(const double *a, const double *b, int n) {
    double m = 0.0;
    for (int i = 0; i < n; i++) {
        double d = fabs(a[i] - b[i]);
        if (d > m) m = d;
    }
    return m;
}

/* Decode test vector's (squares, pieces) arrays into cs_position_t. */
static void load_position(const cs_test_vector_t *tv, cs_position_t *pos)
{
    pos->count = tv->count;
    for (int i = 0; i < tv->count; i++) {
        pos->square[i] = tv->squares[i];
        int code = tv->pieces[i];     /* ±1..±6 */
        int abs_code = code < 0 ? -code : code;
        pos->type[i]  = (uint8_t)(abs_code - 1);  /* 0..5 */
        pos->color[i] = (int8_t)(code < 0 ? -1 : 1);
    }
}

static int check_equal(const char *label, const double *c, const double *ref,
                       int n, double tol, const char *pos_name)
{
    double d = absdiff(c, ref, n);
    if (d > tol) {
        printf("    [FAIL %s @ %s] max |diff| = %.3e (tol %.3e)\n",
               label, pos_name, d, tol);
        return 1;
    }
    return 0;
}

int test_encoder(void)
{
    int fails = 0;
    double sig[64];
    double buf[64];
    cs_encoding_t enc;
    cs_position_t pos;

    for (int ti = 0; ti < CS_TEST_NUM_POSITIONS; ti++) {
        const cs_test_vector_t *tv = &cs_test_vectors[ti];
        load_position(tv, &pos);

        /* 1. board_signal */
        cs_board_signal(&pos, SPECTRAL_VALS, sig);
        fails += check_equal("signal", sig, tv->signal, 64, TOL_CORE, tv->name);

        /* 2. irrep projections */
        for (int k = 0; k < 5; k++) {
            cs_project_irrep(sig, k, buf);
            char lbl[16];
            snprintf(lbl, sizeof(lbl), "irrep%d", k);
            fails += check_equal(lbl, buf, tv->irrep[k], 64, TOL_CORE, tv->name);
        }

        /* 3. symmetric fiber channels */
        for (int d = 0; d < 3; d++) {
            cs_fiber_symmetric_channel(&pos, sig, d, buf);
            char lbl[16];
            snprintf(lbl, sizeof(lbl), "sym%d", d);
            fails += check_equal(lbl, buf, tv->sym[d], 64, TOL_CORE, tv->name);
        }

        /* 4. antisymmetric channel */
        cs_fiber_antisymmetric(&pos, buf);
        fails += check_equal("anti", buf, tv->anti, 64, TOL_CORE, tv->name);

        /* 5. diagonal channel */
        cs_fiber_diagonal(&pos, sig, buf);
        fails += check_equal("diag", buf, tv->diag, 64, TOL_CORE, tv->name);

        /* 6. full 640-dim encoding */
        cs_encode_640(&pos, SPECTRAL_VALS, &enc);
        fails += check_equal("enc640", enc.v, tv->enc640,
                             CS_ENCODING_DIM, TOL_CORE, tv->name);

        /* 7. backward-compat: dims 0..511 == encode_512_spectral */
        fails += check_equal("enc640[0:512]==enc512", enc.v, tv->enc512,
                             512, TOL_BC, tv->name);
    }

    printf("  test_encoder: checked %d positions\n", CS_TEST_NUM_POSITIONS);
    return fails;
}
