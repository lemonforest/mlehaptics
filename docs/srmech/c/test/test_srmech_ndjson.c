/*
 * test_srmech_ndjson.c — C smoke for the streaming NDJSON line reader.
 *
 * Proves srmech_ndjson_iter is byte-faithful after the rc164 retrofit onto
 * the PAL streaming-read surface (srmech_plat_rstream_*). The cases exercise
 * exactly the behaviours that the rstream open/read/close loop must preserve:
 *
 *   - chunk-straddling line assembly: a line longer than the 64 KiB read
 *     chunk must survive being split across two srmech_plat_rstream_read calls;
 *   - empty-line skip: a zero-length line never reaches the callback, but the
 *     1-indexed lineno still advances over it;
 *   - trailing-CR strip ('\r\n' -> line bytes have the CR removed);
 *   - final line with no trailing '\n' is still emitted;
 *   - lineno is 1-indexed over ALL lines (including the skipped empty).
 *
 * The test itself uses stdio to lay down the fixture file (test code is not
 * JPL-bound — only the library is); the library walks it through the PAL.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *msg)
{
    if (cond) {
        g_pass++;
        printf("  PASS  %s\n", msg);
    } else {
        g_fail++;
        printf("  FAIL  %s\n", msg);
    }
}

#define BIG_LINE 70000u   /* > 64 KiB chunk, < 1 MiB max line -> straddles */

/* Recorder threaded through the callback's `user` pointer. */
struct rec {
    int    n;            /* callbacks fired */
    size_t lineno[8];
    size_t len[8];
    char   first[16];    /* bytes of the first emitted line (CR-strip check) */
    char   third[16];    /* bytes of the third emitted line */
};

static srmech_status_t on_line(const char *line, size_t line_len,
                               size_t lineno, void *user)
{
    struct rec *r = (struct rec *)user;
    if (r->n < 8) {
        r->lineno[r->n] = lineno;
        r->len[r->n] = line_len;
        if (r->n == 0 && line_len < sizeof(r->first)) {
            memcpy(r->first, line, line_len);
            r->first[line_len] = '\0';
        }
        if (r->n == 1 && line_len < sizeof(r->third)) {
            memcpy(r->third, line, line_len);
            r->third[line_len] = '\0';
        }
    }
    r->n++;
    return SRMECH_OK;
}

int main(void)
{
    printf("== srmech_ndjson smoke tests (rc164 PAL rstream) ==\n");

    const char *path = "test_ndjson_rc164.tmp";
    FILE *fp = fopen(path, "wb");
    if (fp == NULL) {
        printf("  FAIL  could not create fixture file\n");
        return 1;
    }
    /* line 1: a normal record */
    fputs("{\"a\":1}\n", fp);
    /* line 2: empty (skipped, lineno still advances) */
    fputs("\n", fp);
    /* line 3: trailing CR before LF -> CR must be stripped */
    fputs("{\"b\":2}\r\n", fp);
    /* line 4: a line longer than the 64 KiB read chunk (straddles reads) */
    {
        char *big = (char *)malloc(BIG_LINE);
        memset(big, 'x', BIG_LINE);
        fwrite(big, 1u, BIG_LINE, fp);
        free(big);
        fputs("\n", fp);
    }
    /* line 5: final line with NO trailing newline */
    fputs("tail", fp);
    fclose(fp);

    struct rec r;
    memset(&r, 0, sizeof(r));
    srmech_status_t st = srmech_ndjson_iter(path, on_line, &r);
    remove(path);

    check(st == SRMECH_OK, "iter returns SRMECH_OK");
    check(r.n == 4, "exactly 4 lines emitted (empty line skipped)");
    check(r.lineno[0] == 1u && r.len[0] == 7u, "line 1: lineno 1, 7 bytes");
    check(strcmp(r.first, "{\"a\":1}") == 0, "line 1 bytes verbatim");
    check(r.lineno[1] == 3u && r.len[1] == 7u,
          "line 3: lineno 3 (empty skipped but counted), CR stripped to 7 bytes");
    check(strcmp(r.third, "{\"b\":2}") == 0, "line 3 bytes have the CR removed");
    check(r.lineno[2] == 4u && r.len[2] == BIG_LINE,
          "line 4: 70000-byte line reassembled across the chunk boundary");
    check(r.lineno[3] == 5u && r.len[3] == 4u,
          "line 5: final no-newline line emitted (lineno 5, 4 bytes)");

    /* a missing file is a clean SRMECH_ERR_IO (rstream_open failure path) */
    struct rec r2;
    memset(&r2, 0, sizeof(r2));
    srmech_status_t st2 = srmech_ndjson_iter("no_such_file_rc164.tmp",
                                             on_line, &r2);
    check(st2 == SRMECH_ERR_IO && r2.n == 0,
          "missing file -> SRMECH_ERR_IO, no callbacks");

    printf("== %d passed, %d failed ==\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
