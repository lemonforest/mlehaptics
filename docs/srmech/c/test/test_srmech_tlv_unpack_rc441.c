/*
 * test_srmech_tlv_unpack_rc441.c — the rc441 (`#T1148`) gate for Class B's
 * READER half.
 *
 * WHAT IT ASSERTS. That a BARE-C HOST can walk back a frame it wrote. Through
 * rc440 it could not: `srmech_tlv_pack` shipped in C with no reader anywhere in
 * the library, the reader lived in Python only (srmech/math/tlv.py), and the
 * compiled tool registry — which a C-hosted MCP server serves verbatim — told
 * its users that `tlv_unpack` was "the ONLY correct way to read these frames
 * back". That was advice no C caller could take. A wire format whose whole
 * purpose is to round-trip had exactly one of its two halves projected into C.
 *
 * The rows below are the ones a frame reader gets WRONG when it is wrong:
 *
 *   ROUND TRIP     pack then unpack returns the same tag, the same value bytes,
 *                  and next_offset == 5 + value_len. The empty value (a bare
 *                  five-byte frame) and a 255-byte tag are included because
 *                  both are edge cases of the prefix, not of the payload.
 *   THE WALK       three frames concatenated with NO separator are traversed by
 *                  feeding next_offset back in, and the walk lands on EXACTLY
 *                  the stream length. This is the property that makes the
 *                  format self-delimiting; a reader that mis-sizes any frame
 *                  either overshoots or never terminates.
 *   BIG-ENDIAN     a frame whose length byte pattern differs under the two byte
 *                  orders is read correctly. Reading the length in host order
 *                  is one of the two classic defects of a hand-rolled parser
 *                  and it is invisible on any length below 256.
 *   TRUNCATION     a clipped prefix and a clipped value both DECLINE with
 *                  SRMECH_ERR_BAD_INPUT and write no output. Never partial
 *                  data — the other classic defect is handing back whatever
 *                  bytes remain.
 *   THE WRAP       a frame claiming 0xFFFFFFFF bytes declines. Computed in
 *                  32-bit, value_start + length WRAPS to a small number and the
 *                  end-bound comparison passes, yielding an out-of-bounds span
 *                  from an attacker-supplied length. The kernel computes that
 *                  bound in 64-bit precisely so this row fails closed.
 *   NULL ARGS      a NULL out-pointer is SRMECH_ERR_NULL_ARG, not a crash.
 *
 * NON-VACUITY. Built against a library with the length read little-endian
 * instead of big-endian, this file reports failures on the BIG-ENDIAN and WALK
 * rows and exits 1; against the shipped kernel it exits 0. It cannot pass by
 * not looking.
 *
 * JPL: no malloc, no goto, no recursion; every buffer is a fixed automatic
 * array bounded at compile time.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <stdio.h>
#include <string.h>

static int g_fail = 0;

static void check(int cond, const char *what)
{
    if (!cond) {
        g_fail++;
        printf("  FAIL  %s\n", what);
    }
}

/* One pack->unpack round trip; returns 1 when every field came back intact. */
static int round_trip(uint8_t tag, const uint8_t *value, uint32_t value_len)
{
    uint8_t frame[1024];
    uint32_t written = 0u;
    uint8_t got_tag = 0u;
    uint32_t voff = 0u, vlen = 0u, next = 0u;
    srmech_status_t st;

    st = srmech_tlv_pack(tag, value, value_len, frame,
                         (uint32_t)sizeof frame, &written);
    if (st != SRMECH_OK) { return 0; }
    st = srmech_tlv_unpack(frame, written, 0u, &got_tag, &voff, &vlen, &next);
    if (st != SRMECH_OK) { return 0; }
    if (got_tag != tag || vlen != value_len) { return 0; }
    if (next != value_len + 5u || voff != 5u) { return 0; }
    if (value_len > 0u && memcmp(frame + voff, value, value_len) != 0) {
        return 0;
    }
    return 1;
}

/* The three-frame walk: returns the number of frames traversed, or -1 if the
 * walk failed or did not land on exactly `len`. */
static int walk(const uint8_t *buf, uint32_t len)
{
    uint32_t off = 0u;
    int frames = 0;
    while (off < len) {
        uint8_t tag = 0u;
        uint32_t voff = 0u, vlen = 0u, next = 0u;
        srmech_status_t st = srmech_tlv_unpack(buf, len, off, &tag,
                                               &voff, &vlen, &next);
        if (st != SRMECH_OK) { return -1; }
        if (next <= off) { return -1; }        /* must ADVANCE, or we spin */
        off = next;
        frames++;
        if (frames > 64) { return -1; }        /* bounded: JPL Rule 2 */
    }
    return (off == len) ? frames : -1;
}

int main(void)
{
    uint8_t stream[512];
    uint8_t frame[64];
    uint8_t big[512];
    uint8_t payload[300];
    uint8_t got_tag = 0u;
    uint32_t voff = 0u, vlen = 0u, next = 0u, written = 0u, total = 0u;
    srmech_status_t st;
    uint32_t i;                    /* uint32_t, not unsigned/size_t: every
                                    * length it is compared against or passed
                                    * as is uint32_t, so MSVC /WX sees no
                                    * signed-unsigned or narrowing conversion */

    printf("srmech_tlv_unpack rc441 gate\n");

    /* ---- ROUND TRIP ------------------------------------------------- */
    for (i = 0u; i < (uint32_t)sizeof payload; i++) {
        payload[i] = (uint8_t)(i * 7u);
    }
    check(round_trip(0u, payload, 0u), "round trip: empty value, tag 0");
    check(round_trip(255u, payload, 1u), "round trip: 1-byte value, tag 255");
    check(round_trip(7u, payload, 64u), "round trip: 64-byte value");
    check(round_trip(3u, payload, 300u), "round trip: 300-byte value");

    /* ---- THE WALK: three frames, no separator ------------------------ */
    total = 0u;
    st = srmech_tlv_pack(1u, (const uint8_t *)"10.1093/database/baaa062", 24u,
                         stream, (uint32_t)sizeof stream, &written);
    check(st == SRMECH_OK, "walk: pack frame 1");
    total += written;
    st = srmech_tlv_pack(2u, payload, 64u, stream + total,
                         (uint32_t)sizeof stream - total, &written);
    check(st == SRMECH_OK, "walk: pack frame 2");
    total += written;
    st = srmech_tlv_pack(7u, payload, 200u, stream + total,
                         (uint32_t)sizeof stream - total, &written);
    check(st == SRMECH_OK, "walk: pack frame 3");
    total += written;
    check(walk(stream, total) == 3,
          "walk: next_offset traverses 3 frames to exactly the stream length");

    /* ---- BIG-ENDIAN: a length whose byte pattern is order-sensitive --- */
    st = srmech_tlv_pack(9u, payload, 300u, big, (uint32_t)sizeof big, &written);
    check(st == SRMECH_OK, "big-endian: pack a 300-byte value");
    /* 300 = 0x0000012C. Big-endian prefix bytes are 00 00 01 2C; read in host
     * (little) order the same bytes are 0x2C010000 — a wildly different length,
     * which is why this row and not a short one catches the defect. */
    check(big[1] == 0x00u && big[2] == 0x00u &&
          big[3] == 0x01u && big[4] == 0x2Cu,
          "big-endian: writer laid the length down big-endian");
    st = srmech_tlv_unpack(big, written, 0u, &got_tag, &voff, &vlen, &next);
    check(st == SRMECH_OK && vlen == 300u && next == 305u,
          "big-endian: reader recovers 300, not a byte-swapped length");

    /* ---- TRUNCATION: never partial data ------------------------------ */
    st = srmech_tlv_pack(3u, (const uint8_t *)"ATGCATGC", 8u, frame,
                         (uint32_t)sizeof frame, &written);
    check(st == SRMECH_OK, "truncation: pack the reference frame");
    for (i = 0u; i < 5u; i++) {                 /* every clipped PREFIX */
        st = srmech_tlv_unpack(frame, i, 0u, &got_tag, &voff, &vlen, &next);
        check(st == SRMECH_ERR_BAD_INPUT, "truncation: clipped prefix declines");
    }
    for (i = 5u; i < written; i++) {            /* every clipped VALUE */
        st = srmech_tlv_unpack(frame, i, 0u, &got_tag, &voff, &vlen, &next);
        check(st == SRMECH_ERR_BAD_INPUT, "truncation: clipped value declines");
    }
    /* offset past the end of the buffer */
    st = srmech_tlv_unpack(frame, written, written + 1u, &got_tag,
                           &voff, &vlen, &next);
    check(st == SRMECH_ERR_BAD_INPUT, "truncation: offset past end declines");

    /* ---- THE WRAP: an attacker-supplied length near UINT32_MAX -------- */
    frame[0] = 9u;
    frame[1] = 0xFFu; frame[2] = 0xFFu; frame[3] = 0xFFu; frame[4] = 0xFFu;
    frame[5] = 'x'; frame[6] = 'y';
    st = srmech_tlv_unpack(frame, 7u, 0u, &got_tag, &voff, &vlen, &next);
    check(st == SRMECH_ERR_BAD_INPUT,
          "wrap: length 0xFFFFFFFF declines (64-bit end bound, no wrap)");
    frame[1] = 0xFFu; frame[2] = 0xFFu; frame[3] = 0xFFu; frame[4] = 0xFBu;
    st = srmech_tlv_unpack(frame, 7u, 0u, &got_tag, &voff, &vlen, &next);
    check(st == SRMECH_ERR_BAD_INPUT,
          "wrap: length 0xFFFFFFFB declines (would wrap to 0 in 32-bit)");

    /* ---- NULL ARGS --------------------------------------------------- */
    /* The out-pointer NULL rows are NOT exercised here, deliberately. The
     * house contract on this library is assert-then-return: the JPL Rule 5
     * assertions document the invariant and fire in an assert-enabled build
     * (which is what `make test` produces), while the SRMECH_ERR_NULL_ARG
     * return is defence-in-depth for an NDEBUG build. `srmech_tlv_pack`
     * next door has exactly the same shape. So passing NULL here would
     * abort the process rather than measure a status, and a gate that
     * core-dumps is not a gate. The one NULL row that IS decidable in this
     * build is the buffer, because its guard is reached before the assert:
     * an EMPTY buffer is not a null-arg case at all — it is a truncated
     * prefix, and the two must not be conflated. */
    st = srmech_tlv_unpack(NULL, 0u, 0u, &got_tag, &voff, &vlen, &next);
    check(st == SRMECH_ERR_BAD_INPUT, "null: empty buffer is BAD_INPUT, not NULL_ARG");

    printf("== srmech_tlv_unpack: %d failure(s) ==\n", g_fail);
    return g_fail == 0 ? 0 : 1;
}
