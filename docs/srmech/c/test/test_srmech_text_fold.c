/*
 * test_srmech_text_fold.c — rc293 (#928 / F1258) bare-C-HOST smoke for
 * srmech_text_fold_marks + srmech_text_default_fold_table.
 *
 * THIS FILE IS THE ADR-0003 CLAIM UNDER TEST, not a convenience harness.
 * `fold_marks` is the first text op whose data a host COULD have derived
 * from Python (`unicodedata` exposes category + decomposition, unlike the
 * UAX #29 properties rc287 needed). The reason it does not is that a
 * bare-C host has no Python at all — so the only way to know the vendored
 * table actually serves such a host is to link one with no Python present
 * and fold real multi-script text through it. That is this file.
 *
 * Runtime if-guards, not assert(), so it is a real value check even under
 * Release/NDEBUG, and it joins the -Werror/-WX pedantic gate.
 *
 * Run it:  ./build/test_srmech_text_fold        (exit 0 = all pass)
 */
#include "srmech.h"
#include "srmech_unicode_fold_tables.h"

#include <stdio.h>
#include <string.h>

static int g_fail;

/* Fold `in` with the srmech-shipped DEFAULT table and compare to `want`. */
static void check(const char *label, const char *in, const char *want)
{
    const uint32_t *lo, *hi, *rep;
    size_t          n_ranges, out_len;
    uint8_t         out[256];
    srmech_status_t st;

    srmech_text_default_fold_table(&lo, &hi, &rep, &n_ranges);
    if (lo == NULL || hi == NULL || rep == NULL || n_ranges == 0u) {
        printf("FAIL %-24s default table not served\n", label);
        g_fail++;
        return;
    }
    st = srmech_text_fold_marks((const uint8_t *)in, strlen(in),
                                lo, hi, rep, n_ranges,
                                out, sizeof(out) - 1u, &out_len);
    if (st != SRMECH_OK) {
        printf("FAIL %-24s status=%d\n", label, (int)st);
        g_fail++;
        return;
    }
    out[out_len] = (uint8_t)0;
    if (strcmp((const char *)out, want) != 0) {
        printf("FAIL %-24s got=<%s> want=<%s>\n", label, (char *)out, want);
        g_fail++;
        return;
    }
    printf("ok   %-24s <%s> -> <%s>\n", label, in, (char *)out);
}

/* Assert a status without caring about the output bytes. */
static void check_status(const char *label, const char *in, size_t in_len,
                         size_t cap, srmech_status_t want)
{
    const uint32_t *lo, *hi, *rep;
    size_t          n_ranges, out_len;
    uint8_t         out[8];
    srmech_status_t st;

    srmech_text_default_fold_table(&lo, &hi, &rep, &n_ranges);
    if (cap > sizeof(out)) { cap = sizeof(out); }
    st = srmech_text_fold_marks((const uint8_t *)in, in_len,
                                lo, hi, rep, n_ranges,
                                out, cap, &out_len);
    if (st != want) {
        printf("FAIL %-24s status=%d want=%d\n", label, (int)st, (int)want);
        g_fail++;
        return;
    }
    printf("ok   %-24s status=%d\n", label, (int)st);
}

int main(void)
{
    printf("srmech %s — fold table UCD %s, %u ranges, sha256 %.16s...\n",
           SRMECH_VERSION, SRMECH_FOLD_UCD_VERSION,
           (unsigned)SRMECH_FOLD_RANGE_COUNT, SRMECH_FOLD_TABLE_SHA256);

    /* The Latin case: precomposed and decomposed must agree, which is the
     * whole reason the op needs no normalizer. */
    check("latin precomposed", "na\xc3\xafve", "naive");
    check("latin decomposed",  "nai\xcc\x88ve", "naive");
    check("stacked marks",     "\xe1\xba\xbf", "e");        /* U+1EBF */

    /* The naming argument: a VIRAMA is a mark. क्षि -> कष. */
    check("virama + vowel sign",
          "\xe0\xa4\x95\xe0\xa5\x8d\xe0\xa4\xb7\xe0\xa4\xbf",
          "\xe0\xa4\x95\xe0\xa4\xb7");

    /* Category-only scope: these must NOT change. */
    check("hangul kept",   "\xed\x95\x9c", "\xed\x95\x9c");        /* 한 */
    check("stroke kept",   "\xc3\xb8", "\xc3\xb8");                /* ø   */
    check("ohm sign kept", "\xe2\x84\xa6", "\xe2\x84\xa6");        /* Ω   */
    check("cjk kept",      "\xe6\x97\xa5\xe6\x9c\xac", "\xe6\x97\xa5\xe6\x9c\xac");
    check("emoji kept",    "\xf0\x9f\x91\x8d", "\xf0\x9f\x91\x8d");
    check("ascii passthru", "hello, world!", "hello, world!");

    /* Degenerate inputs. */
    check("empty",     "", "");
    check("lone mark", "\xcc\x81", "");                            /* U+0301 */
    check("only marks", "\xcc\x81\xcc\x82\xcc\x83", "");

    /* Contract edges are REPORTED, never wrapped or silently truncated. */
    check_status("overflow reported", "abcdefghij", 10u, 2u,
                 SRMECH_ERR_OVERFLOW);
    check_status("malformed utf-8", "\xff\xfe", 2u, 8u,
                 SRMECH_ERR_BAD_INPUT);
    check_status("truncated utf-8", "\xc3", 1u, 8u,
                 SRMECH_ERR_BAD_INPUT);

    if (g_fail != 0) {
        printf("\n%d FAILURE(S)\n", g_fail);
        return 1;
    }
    printf("\nall bare-C fold checks passed\n");
    return 0;
}
