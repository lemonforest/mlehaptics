/*
 * srmech_carrier.c — the Mat/Vec CARRIER struct + C API (0.9.0rc141;
 * Foundation F0, the LAST C:Python parity backfill foundation).
 *
 * THE GAP this closes. srmech's numeric compute KERNELS were already C
 * (srmech_dense_matmul_complex / srmech_svd_f64 / srmech_fft_c128 …) and read
 * the Python Mat/Vec `array('d')` buffers ZERO-COPY. But the carrier OBJECT —
 * construction, get/set, the row/col views, the elementwise arithmetic,
 * .conj/.T, the buffer sizing/lifecycle — lived ONLY in Python (mat.py /
 * vec.py). So a BARE C HOST (a microcontroller, a no-Python embed) could call
 * the kernels but could not HOLD or MANIPULATE a carrier: it had to hand-roll
 * the row-major / interleaved-(re,im) layout itself. This file gives the C
 * host the carrier vocabulary — build a carrier, index it, do elementwise
 * math, conjugate/transpose, then feed the SAME buffer straight to the compute
 * kernels — with no Python present. The everything-mirrors capstone.
 *
 * THE CARRIER STRUCT (mirrors the Python Mat/Vec layout exactly):
 *
 *   srmech_mat_t { double *buf; uint32_t rows, cols; int is_complex; }
 *   srmech_vec_t { double *buf; uint32_t n;          int is_complex; }
 *
 *   - buf is CALLER-OWNED (JPL Rule 3: no malloc — the struct is a view over a
 *     backing store the caller provides, exactly like srmech_bigint_t's
 *     caller-owned `limbs`). Row-major.
 *   - real    : one double per element  (rows*cols / n doubles).
 *   - complex : interleaved (re, im)    (2*rows*cols / 2*n doubles) = C99
 *     `double _Complex` memory order, so buf is byte-identical to the Python
 *     carrier's `array('d')` and feeds the interleaved-complex kernels no-copy.
 *
 * BYTE-IDENTICAL to the Python carrier. Every value op computes with the SAME
 * IEEE-754 operation order CPython uses: complex multiply is the naive
 * (ac - bd) + (ad + bc)i (CPython `_Py_c_prod`), add/sub are componentwise, so
 * the C result is bit-for-bit the Python Mat/Vec result. (Division is NOT in
 * the C surface: CPython uses Smith's scaled algorithm for complex `/`, so a
 * byte-identical C twin would have to re-derive it — the carrier's `/` stays
 * the pure-Python path, the complete + byte-exact oracle.)
 *
 * NO abs(). Every sign move is a Class-K pin-slot: conj negates the imaginary
 * slot, neg negates every slot — a branch/negate, never a magnitude fold.
 *
 * FORMAT-PRESERVING dtype rule (mirrors the Python carriers): real op real ->
 * real; a complex operand (or a scalar with a NON-ZERO imaginary part)
 * promotes the result to complex. The caller provides `out` already shaped to
 * that rule; a mismatch returns SRMECH_ERR_BAD_INPUT (never a silent wrong
 * layout).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion) : straight-line loops.
 *   - Rule 2 (bounded loops)     : every loop bounded by rows/cols/n.
 *   - Rule 3 (no malloc)         : caller-owned buffers only.
 *   - Rule 4 (<=60 lines/func)   : small helpers + thin public wrappers.
 *   - Rule 5 (>=2 asserts/fn)    : pointer / shape / dtype pre-conditions.
 *   - Rule 7 (return-value)      : srmech_status_t on every entry.
 *   - Rule 8 (no multi-line macro): a single plain enum, no macros.
 *   - Rule 10 (warnings clean)   : -Wall -Wextra -Wpedantic -Werror / /WX,
 *                                  both -O2 (asserts live) and -DNDEBUG.
 *
 * ABI: new symbols only — SRMECH_ABI_VERSION stays 3 (additive; the Python
 * ctypes shim hasattr-guards every binding).
 *
 * License: MIT (parent project: mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Elementwise op selectors (a plain enum — JPL Rule 8: no macros). */
enum {
    CARRIER_OP_ADD = 0,
    CARRIER_OP_SUB = 1,
    CARRIER_OP_MUL = 2
};

/* ------------------------------------------------------------------ *
 * Flat-buffer value cores (shared by Mat + Vec — the layout is the
 * same flat interleaved buffer; only the element COUNT differs).
 * ------------------------------------------------------------------ */

/* out[i] = a[i] (op) b[i] over `n` elements, promoting each operand to a
 * (re, im) pair per its own is_complex flag and writing per out_cplx. The
 * complex product is the naive CPython `_Py_c_prod` form -> byte-identical. */
static srmech_status_t carrier_binary_flat(
    const double *a, int a_cplx, const double *b, int b_cplx,
    double *out, int out_cplx, size_t n, int op)
{
    size_t i;
    assert(a != NULL);
    assert(b != NULL);
    assert(out != NULL);
    for (i = 0; i < n; ++i) {
        double ar = a_cplx ? a[2 * i] : a[i];
        double ai = a_cplx ? a[2 * i + 1] : 0.0;
        double br = b_cplx ? b[2 * i] : b[i];
        double bi = b_cplx ? b[2 * i + 1] : 0.0;
        double orr, oii;
        if (op == CARRIER_OP_ADD) {
            orr = ar + br;
            oii = ai + bi;
        } else if (op == CARRIER_OP_SUB) {
            orr = ar - br;
            oii = ai - bi;
        } else {
            orr = ar * br - ai * bi;
            oii = ar * bi + ai * br;
        }
        if (out_cplx) {
            out[2 * i] = orr;
            out[2 * i + 1] = oii;
        } else {
            out[i] = orr;
            (void)oii;
        }
    }
    return SRMECH_OK;
}

/* out[i] = a[i] (op) scalar(s_re, s_im). op == CARRIER_OP_ADD adds the scalar,
 * anything else multiplies (scale). Byte-identical to Python's scalar
 * broadcast (`_Py_c_prod` for the complex scale). */
static srmech_status_t carrier_scalar_flat(
    const double *a, int a_cplx, double s_re, double s_im,
    double *out, int out_cplx, size_t n, int op)
{
    size_t i;
    assert(a != NULL);
    assert(out != NULL);
    for (i = 0; i < n; ++i) {
        double ar = a_cplx ? a[2 * i] : a[i];
        double ai = a_cplx ? a[2 * i + 1] : 0.0;
        double orr, oii;
        if (op == CARRIER_OP_ADD) {
            orr = ar + s_re;
            oii = ai + s_im;
        } else {
            orr = ar * s_re - ai * s_im;
            oii = ar * s_im + ai * s_re;
        }
        if (out_cplx) {
            out[2 * i] = orr;
            out[2 * i + 1] = oii;
        } else {
            out[i] = orr;
            (void)oii;
        }
    }
    return SRMECH_OK;
}

/* out[i] = a[i] with an optional Class-K sign flip on the real / imaginary
 * slot (conj: imag only; neg: both; copy: neither). No abs — a pure negate. */
static srmech_status_t carrier_unary_flat(
    const double *a, double *out, int cplx, size_t n, int neg_re, int neg_im)
{
    size_t i;
    assert(a != NULL);
    assert(out != NULL);
    for (i = 0; i < n; ++i) {
        if (cplx) {
            out[2 * i] = neg_re ? -a[2 * i] : a[2 * i];
            out[2 * i + 1] = neg_im ? -a[2 * i + 1] : a[2 * i + 1];
        } else {
            out[i] = neg_re ? -a[i] : a[i];
            (void)neg_im;
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Sizing (how big a backing buffer the caller must provide).
 * ------------------------------------------------------------------ */

size_t srmech_mat_buf_len(uint32_t rows, uint32_t cols, int is_complex)
{
    size_t elems = (size_t)rows * (size_t)cols;
    size_t stride = is_complex ? (size_t)2 : (size_t)1;
    assert(rows == 0u || elems / (size_t)rows == (size_t)cols); /* no overflow */
    assert(stride == (size_t)1 || stride == (size_t)2);
    return stride * elems;
}

size_t srmech_vec_buf_len(uint32_t n, int is_complex)
{
    size_t stride = is_complex ? (size_t)2 : (size_t)1;
    assert(stride == (size_t)1 || stride == (size_t)2);
    assert((size_t)n <= ((size_t)-1) / stride); /* no size_t overflow */
    return stride * (size_t)n;
}

/* ------------------------------------------------------------------ *
 * Construction (a view over a caller buffer; zeros = view + clear).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_mat_init(srmech_mat_t *m, double *buf,
                                uint32_t rows, uint32_t cols, int is_complex)
{
    assert(m != NULL);
    assert(buf != NULL);
    if (m == NULL || buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    m->buf = buf;
    m->rows = rows;
    m->cols = cols;
    m->is_complex = is_complex ? 1 : 0;
    return SRMECH_OK;
}

srmech_status_t srmech_vec_init(srmech_vec_t *v, double *buf,
                                uint32_t n, int is_complex)
{
    assert(v != NULL);
    assert(buf != NULL);
    if (v == NULL || buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    v->buf = buf;
    v->n = n;
    v->is_complex = is_complex ? 1 : 0;
    return SRMECH_OK;
}

srmech_status_t srmech_mat_zeros(srmech_mat_t *m, double *buf,
                                 uint32_t rows, uint32_t cols, int is_complex)
{
    size_t len;
    size_t i;
    srmech_status_t st;
    assert(m != NULL);
    assert(buf != NULL);
    st = srmech_mat_init(m, buf, rows, cols, is_complex);
    if (st != SRMECH_OK) {
        return st;
    }
    len = srmech_mat_buf_len(rows, cols, m->is_complex);
    for (i = 0; i < len; ++i) {
        buf[i] = 0.0;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_vec_zeros(srmech_vec_t *v, double *buf,
                                 uint32_t n, int is_complex)
{
    size_t len;
    size_t i;
    srmech_status_t st;
    assert(v != NULL);
    assert(buf != NULL);
    st = srmech_vec_init(v, buf, n, is_complex);
    if (st != SRMECH_OK) {
        return st;
    }
    len = srmech_vec_buf_len(n, v->is_complex);
    for (i = 0; i < len; ++i) {
        buf[i] = 0.0;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Element accessors. get writes *re_out (+ *im_out if non-NULL, 0 for a
 * real carrier); set stores (re[, im]) — a real carrier ignores im, as
 * the Python carrier stores only float(x.real).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_mat_get(const srmech_mat_t *m, uint32_t i, uint32_t j,
                               double *re_out, double *im_out)
{
    size_t flat;
    assert(m != NULL);
    assert(re_out != NULL);
    if (m == NULL || m->buf == NULL || re_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (i >= m->rows || j >= m->cols) {
        return SRMECH_ERR_BAD_INPUT;
    }
    flat = (size_t)i * (size_t)m->cols + (size_t)j;
    if (m->is_complex) {
        *re_out = m->buf[2 * flat];
        if (im_out != NULL) {
            *im_out = m->buf[2 * flat + 1];
        }
    } else {
        *re_out = m->buf[flat];
        if (im_out != NULL) {
            *im_out = 0.0;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_mat_set(srmech_mat_t *m, uint32_t i, uint32_t j,
                               double re, double im)
{
    size_t flat;
    assert(m != NULL);
    assert(m->buf != NULL);
    if (m == NULL || m->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (i >= m->rows || j >= m->cols) {
        return SRMECH_ERR_BAD_INPUT;
    }
    flat = (size_t)i * (size_t)m->cols + (size_t)j;
    if (m->is_complex) {
        m->buf[2 * flat] = re;
        m->buf[2 * flat + 1] = im;
    } else {
        m->buf[flat] = re;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_vec_get(const srmech_vec_t *v, uint32_t i,
                               double *re_out, double *im_out)
{
    assert(v != NULL);
    assert(re_out != NULL);
    if (v == NULL || v->buf == NULL || re_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (i >= v->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (v->is_complex) {
        *re_out = v->buf[2 * (size_t)i];
        if (im_out != NULL) {
            *im_out = v->buf[2 * (size_t)i + 1];
        }
    } else {
        *re_out = v->buf[(size_t)i];
        if (im_out != NULL) {
            *im_out = 0.0;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_vec_set(srmech_vec_t *v, uint32_t i, double re, double im)
{
    assert(v != NULL);
    assert(v->buf != NULL);
    if (v == NULL || v->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (i >= v->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (v->is_complex) {
        v->buf[2 * (size_t)i] = re;
        v->buf[2 * (size_t)i + 1] = im;
    } else {
        v->buf[(size_t)i] = re;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Row / column views (copied into a caller-provided Vec of matching
 * length + dtype — mirrors Python m[i] / m[:, j] -> Vec).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_mat_row(const srmech_mat_t *m, uint32_t i,
                               srmech_vec_t *out)
{
    uint32_t j;
    assert(m != NULL);
    assert(out != NULL);
    if (m == NULL || out == NULL || m->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (i >= m->rows || out->n != m->cols) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if ((out->is_complex ? 1 : 0) != (m->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (j = 0; j < m->cols; ++j) {
        double re, im;
        srmech_status_t st = srmech_mat_get(m, i, j, &re, &im);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_vec_set(out, j, re, im);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_mat_col(const srmech_mat_t *m, uint32_t j,
                               srmech_vec_t *out)
{
    uint32_t i;
    assert(m != NULL);
    assert(out != NULL);
    if (m == NULL || out == NULL || m->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (j >= m->cols || out->n != m->rows) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if ((out->is_complex ? 1 : 0) != (m->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (i = 0; i < m->rows; ++i) {
        double re, im;
        srmech_status_t st = srmech_mat_get(m, i, j, &re, &im);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_vec_set(out, i, re, im);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Elementwise binary (carrier (op) carrier). out->is_complex MUST equal
 * a|b (the format-preserving rule) or SRMECH_ERR_BAD_INPUT.
 * ------------------------------------------------------------------ */

static srmech_status_t mat_binary(const srmech_mat_t *a, const srmech_mat_t *b,
                                  srmech_mat_t *out, int op)
{
    int want, have;
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || b == NULL || out == NULL
        || a->buf == NULL || b->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (a->rows != b->rows || a->cols != b->cols
        || out->rows != a->rows || out->cols != a->cols) {
        return SRMECH_ERR_BAD_INPUT;
    }
    want = (a->is_complex ? 1 : 0) | (b->is_complex ? 1 : 0);
    have = out->is_complex ? 1 : 0;
    if (have != want) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_binary_flat(a->buf, a->is_complex, b->buf, b->is_complex,
                               out->buf, have,
                               (size_t)a->rows * (size_t)a->cols, op);
}

srmech_status_t srmech_mat_add(const srmech_mat_t *a, const srmech_mat_t *b,
                               srmech_mat_t *out)
{
    assert(a != NULL);
    assert(b != NULL);
    return mat_binary(a, b, out, CARRIER_OP_ADD);
}

srmech_status_t srmech_mat_sub(const srmech_mat_t *a, const srmech_mat_t *b,
                               srmech_mat_t *out)
{
    assert(a != NULL);
    assert(b != NULL);
    return mat_binary(a, b, out, CARRIER_OP_SUB);
}

srmech_status_t srmech_mat_mul(const srmech_mat_t *a, const srmech_mat_t *b,
                               srmech_mat_t *out)
{
    assert(a != NULL);
    assert(b != NULL);
    return mat_binary(a, b, out, CARRIER_OP_MUL);
}

static srmech_status_t vec_binary(const srmech_vec_t *a, const srmech_vec_t *b,
                                  srmech_vec_t *out, int op)
{
    int want, have;
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || b == NULL || out == NULL
        || a->buf == NULL || b->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (a->n != b->n || out->n != a->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    want = (a->is_complex ? 1 : 0) | (b->is_complex ? 1 : 0);
    have = out->is_complex ? 1 : 0;
    if (have != want) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_binary_flat(a->buf, a->is_complex, b->buf, b->is_complex,
                               out->buf, have, (size_t)a->n, op);
}

srmech_status_t srmech_vec_add(const srmech_vec_t *a, const srmech_vec_t *b,
                               srmech_vec_t *out)
{
    assert(a != NULL);
    assert(b != NULL);
    return vec_binary(a, b, out, CARRIER_OP_ADD);
}

srmech_status_t srmech_vec_sub(const srmech_vec_t *a, const srmech_vec_t *b,
                               srmech_vec_t *out)
{
    assert(a != NULL);
    assert(b != NULL);
    return vec_binary(a, b, out, CARRIER_OP_SUB);
}

srmech_status_t srmech_vec_mul(const srmech_vec_t *a, const srmech_vec_t *b,
                               srmech_vec_t *out)
{
    assert(a != NULL);
    assert(b != NULL);
    return vec_binary(a, b, out, CARRIER_OP_MUL);
}

/* ------------------------------------------------------------------ *
 * Scalar broadcast. out->is_complex MUST equal a|(s_im != 0) — a scalar
 * with a NON-ZERO imaginary part promotes, matching the Python rule
 * (isinstance(other, complex) and other.imag != 0.0).
 * ------------------------------------------------------------------ */

static srmech_status_t mat_scalar(const srmech_mat_t *a, double s_re,
                                  double s_im, srmech_mat_t *out, int op)
{
    int want, have;
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->rows != a->rows || out->cols != a->cols) {
        return SRMECH_ERR_BAD_INPUT;
    }
    want = (a->is_complex ? 1 : 0) | (s_im != 0.0 ? 1 : 0);
    have = out->is_complex ? 1 : 0;
    if (have != want) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_scalar_flat(a->buf, a->is_complex, s_re, s_im,
                               out->buf, have,
                               (size_t)a->rows * (size_t)a->cols, op);
}

srmech_status_t srmech_mat_scale(const srmech_mat_t *a, double s_re,
                                 double s_im, srmech_mat_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    return mat_scalar(a, s_re, s_im, out, CARRIER_OP_MUL);
}

srmech_status_t srmech_mat_add_scalar(const srmech_mat_t *a, double s_re,
                                      double s_im, srmech_mat_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    return mat_scalar(a, s_re, s_im, out, CARRIER_OP_ADD);
}

static srmech_status_t vec_scalar(const srmech_vec_t *a, double s_re,
                                  double s_im, srmech_vec_t *out, int op)
{
    int want, have;
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->n != a->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    want = (a->is_complex ? 1 : 0) | (s_im != 0.0 ? 1 : 0);
    have = out->is_complex ? 1 : 0;
    if (have != want) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_scalar_flat(a->buf, a->is_complex, s_re, s_im,
                               out->buf, have, (size_t)a->n, op);
}

srmech_status_t srmech_vec_scale(const srmech_vec_t *a, double s_re,
                                 double s_im, srmech_vec_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    return vec_scalar(a, s_re, s_im, out, CARRIER_OP_MUL);
}

srmech_status_t srmech_vec_add_scalar(const srmech_vec_t *a, double s_re,
                                      double s_im, srmech_vec_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    return vec_scalar(a, s_re, s_im, out, CARRIER_OP_ADD);
}

/* ------------------------------------------------------------------ *
 * Unary. conj = Class-K sign flip on the imaginary slot (real -> copy);
 * neg = sign flip on every slot; transpose rearranges (dtype preserved).
 * out shape/dtype must match (conj/neg: same shape; transpose: swapped).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_mat_conj(const srmech_mat_t *a, srmech_mat_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->rows != a->rows || out->cols != a->cols
        || (out->is_complex ? 1 : 0) != (a->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_unary_flat(a->buf, out->buf, a->is_complex,
                              (size_t)a->rows * (size_t)a->cols, 0, 1);
}

srmech_status_t srmech_mat_neg(const srmech_mat_t *a, srmech_mat_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->rows != a->rows || out->cols != a->cols
        || (out->is_complex ? 1 : 0) != (a->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_unary_flat(a->buf, out->buf, a->is_complex,
                              (size_t)a->rows * (size_t)a->cols, 1, 1);
}

srmech_status_t srmech_mat_transpose(const srmech_mat_t *a, srmech_mat_t *out)
{
    uint32_t i, j;
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->rows != a->cols || out->cols != a->rows
        || (out->is_complex ? 1 : 0) != (a->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (i = 0; i < a->rows; ++i) {
        for (j = 0; j < a->cols; ++j) {
            double re, im;
            srmech_status_t st = srmech_mat_get(a, i, j, &re, &im);
            if (st != SRMECH_OK) {
                return st;
            }
            st = srmech_mat_set(out, j, i, re, im);
            if (st != SRMECH_OK) {
                return st;
            }
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_vec_conj(const srmech_vec_t *a, srmech_vec_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->n != a->n || (out->is_complex ? 1 : 0) != (a->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_unary_flat(a->buf, out->buf, a->is_complex,
                              (size_t)a->n, 0, 1);
}

srmech_status_t srmech_vec_neg(const srmech_vec_t *a, srmech_vec_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL || a->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out->n != a->n || (out->is_complex ? 1 : 0) != (a->is_complex ? 1 : 0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return carrier_unary_flat(a->buf, out->buf, a->is_complex,
                              (size_t)a->n, 1, 1);
}

/* ------------------------------------------------------------------ *
 * The zero-copy KERNEL BRIDGE: a complex carrier matmul that feeds the
 * three carrier buffers STRAIGHT to srmech_dense_matmul_complex (no copy,
 * no reshape) — the demonstration that a C host builds carriers with this
 * API and hands them to the existing compute kernels Python-free. Real /
 * SVD / FFT bridges need no wrapper at all: the carrier buf IS the
 * row-major (real) / interleaved-complex argument those kernels already
 * take (a->buf passes directly).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_mat_matmul_c128(const srmech_mat_t *a,
                                       const srmech_mat_t *b, srmech_mat_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || b == NULL || out == NULL
        || a->buf == NULL || b->buf == NULL || out->buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (!a->is_complex || !b->is_complex || !out->is_complex) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (a->cols != b->rows || out->rows != a->rows || out->cols != b->cols) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return srmech_dense_matmul_complex(a->rows, a->cols, b->cols,
                                       a->buf, b->buf, out->buf);
}
