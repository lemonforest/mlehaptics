/* test_srmech_genome_group_rc442.c — the GROUP/v20 nesting grammar, from bare C.
 *
 * rc442 (task T1150). ADR-0003 says the C host stands alone: a bare-C host with no
 * Python present must be able to MINT a group and WALK one, and must refuse every
 * malformed strand the Python projection refuses. This file is that claim, executable.
 *
 * It is deliberately NOT a differential test — the Python side owns that
 * (tests/test_genome_group_v20_rc442.py drives both projections over random nested
 * strands). What this file holds is the half a differential CANNOT: that the C surface
 * is usable ON ITS OWN, with no oracle to compare against and nothing to fall back to.
 *
 * Build + run:
 *   ctest -R test_srmech_genome_group_rc442
 *   ./build/test_srmech_genome_group_rc442      (exit 0 = all pass)
 *
 * No malloc, no goto, no recursion, no float, no abs. */

#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

#define DIM 16u
#define MAXB 64u

static int failures = 0;

static void check(int cond, const char *what)
{
    assert(what != NULL);
    assert(DIM > 0u);
    if (cond) {
        printf("  ok   %s\n", what);
        return;
    }
    printf("  FAIL %s\n", what);
    failures++;
}

/* Write a CHROM cap + `n` Klein-4 data turns at blocks[*n_blocks]. */
static void put_chrom(unsigned char *blocks, size_t *n_blocks,
                      const char *label, size_t n_turns)
{
    assert(blocks != NULL && n_blocks != NULL);
    assert(label != NULL);
    unsigned char *p = blocks + (*n_blocks) * DIM;
    memset(p, 0, DIM);
    p[0] = SRMECH_GENOME_CHROM_CAP_MARKER;
    memcpy(p + 1, label, strlen(label));
    (*n_blocks)++;
    for (size_t i = 0; i < n_turns; i++) {
        unsigned char *t = blocks + (*n_blocks) * DIM;
        for (size_t k = 0; k < DIM; k++) { t[k] = (unsigned char)((i + k) & 3u); }
        (*n_blocks)++;
    }
}

static void put_marker(unsigned char *blocks, size_t *n_blocks,
                       unsigned char marker, const char *label)
{
    assert(blocks != NULL && n_blocks != NULL);
    assert(marker > 3u);
    unsigned char *p = blocks + (*n_blocks) * DIM;
    memset(p, 0, DIM);
    p[0] = marker;
    if (label != NULL) { memcpy(p + 1, label, strlen(label)); }
    (*n_blocks)++;
}

/* A bare-C host MINTS a group, then reads back what it wrote. */
static void test_wrap_then_walk(void)
{
    unsigned char sub[MAXB * DIM];
    unsigned char out[MAXB * DIM];
    srmech_genome_group_t recs[8];
    size_t n_sub = 0u, n_out = 0u;
    uint32_t n_recs = 0u;
    printf("wrap-then-walk\n");
    put_chrom(sub, &n_sub, "aa", 2u);
    put_chrom(sub, &n_sub, "bb", 2u);
    srmech_status_t st = srmech_genome_group_wrap(
        sub, n_sub, DIM, (const unsigned char *)"sy", 2u, out, sizeof(out), &n_out);
    check(st == SRMECH_OK, "wrap returns SRMECH_OK");
    check(n_out == n_sub + 2u, "wrap adds exactly two blocks");
    check(out[0] == SRMECH_GENOME_GROUP_OPEN_MARKER, "block 0 is the opener");
    check(out[(n_out - 1u) * DIM] == SRMECH_GENOME_GROUP_CLOSE_MARKER,
          "the last block is the closer");
    /* THE CLOSER CARRIES NOTHING — every byte after the marker is NUL. */
    int payload = 0;
    for (size_t k = 1; k < DIM; k++) {
        if (out[(n_out - 1u) * DIM + k] != 0u) { payload = 1; }
    }
    check(payload == 0, "the closer carries no label and no depth");
    check(memcmp(out + DIM, sub, n_sub * DIM) == 0, "the subject rides verbatim");

    st = srmech_genome_group_walk(out, n_out, DIM, recs, 8u, &n_recs);
    check(st == SRMECH_OK, "walk accepts what wrap wrote");
    check(n_recs == 1u, "one group");
    check(recs[0].open_idx == 0u && recs[0].close_idx == n_out - 1u,
          "the record spans the whole strand");
    check(recs[0].depth == 0u, "a top-level group is at depth 0");
    check(recs[0].arity == 2u, "arity counts the two chromosomes");
    check(strcmp(recs[0].label, "sy") == 0, "the label comes off the OPENER");
}

/* out=NULL is the documented validate-only shape: the count still comes back. */
static void test_validate_only(void)
{
    unsigned char sub[MAXB * DIM];
    unsigned char out[MAXB * DIM];
    size_t n_sub = 0u, n_out = 0u;
    uint32_t n_recs = 99u;
    printf("validate-only (out == NULL)\n");
    put_chrom(sub, &n_sub, "aa", 1u);
    srmech_status_t st = srmech_genome_group_wrap(
        sub, n_sub, DIM, (const unsigned char *)"g", 1u, out, sizeof(out), &n_out);
    check(st == SRMECH_OK, "wrap ok");
    st = srmech_genome_group_walk(out, n_out, DIM, NULL, 0u, &n_recs);
    check(st == SRMECH_OK, "validate-only returns OK");
    check(n_recs == 1u, "and still counts the groups");
}

/* A group of ONE is legal; a group of NONE is not. Banning arity 1 would be the
 * same constraint error as banning arity 0, only in the opposite direction. */
static void test_arity(void)
{
    unsigned char b[MAXB * DIM];
    size_t n = 0u;
    uint32_t n_recs = 0u;
    printf("arity\n");
    put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "solo");
    put_chrom(b, &n, "aa", 1u);
    put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs) == SRMECH_OK,
          "a group of ONE is legal");
    n = 0u;
    put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "empty");
    put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs)
          == SRMECH_ERR_BAD_INPUT, "a childless group is refused");
}

/* Every malformed class is refused, and each in ONE forward pass. */
static void test_malformed(void)
{
    unsigned char b[MAXB * DIM];
    size_t n = 0u;
    uint32_t n_recs = 0u;
    printf("malformed classes\n");

    n = 0u;                                   /* closer without opener */
    put_chrom(b, &n, "aa", 1u);
    put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs)
          == SRMECH_ERR_BAD_INPUT, "closer-without-opener refused");

    n = 0u;                                   /* unclosed opener */
    put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "x");
    put_chrom(b, &n, "aa", 1u);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs)
          == SRMECH_ERR_BAD_INPUT, "unclosed-opener refused");

    n = 0u;                                   /* R3: a turn at group scope */
    put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "x");
    memset(b + n * DIM, 1, DIM);              /* a bare Klein-4 data turn */
    n++;
    put_chrom(b, &n, "aa", 1u);
    put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs)
          == SRMECH_ERR_BAD_INPUT, "turn-at-group-scope refused (R3)");

    /* R4: crossed nesting. The group opens INSIDE chromosome 'aa' and closes after
     * 'bb'. It is refused not as a special case but because R3 already forbids the
     * turn that follows the opener — which is what makes crossing UNREPRESENTABLE
     * rather than merely detected. */
    n = 0u;
    put_chrom(b, &n, "aa", 1u);
    put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "x");
    memset(b + n * DIM, 2, DIM);
    n++;
    put_chrom(b, &n, "bb", 1u);
    put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs)
          == SRMECH_ERR_BAD_INPUT, "crossed nesting is unrepresentable (R4)");
}

/* Depth overflow is SRMECH_ERR_LIMIT, never SRMECH_ERR_OVERFLOW. rc404 defines
 * LIMIT as a compiled-in cap where retrying is futile BY CONSTRUCTION; OVERFLOW
 * means "your buffer was too small" and would send a grow-loop into futile
 * doubling against a bound no buffer can move. */
static void test_depth_limit(void)
{
    static unsigned char b[(2u * SRMECH_GENOME_MAX_GROUP_DEPTH + 8u) * DIM];
    size_t n = 0u;
    uint32_t n_recs = 0u;
    printf("depth cap\n");
    for (uint32_t d = 0; d < SRMECH_GENOME_MAX_GROUP_DEPTH; d++) {
        put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "d");
    }
    put_chrom(b, &n, "aa", 1u);
    for (uint32_t d = 0; d < SRMECH_GENOME_MAX_GROUP_DEPTH; d++) {
        put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    }
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs) == SRMECH_OK,
          "nesting AT the cap is legal");
    check(n_recs == SRMECH_GENOME_MAX_GROUP_DEPTH, "and reports every frame");

    /* One deeper. Rebuild rather than splice, so the strand stays well-formed
     * except for the depth. */
    n = 0u;
    for (uint32_t d = 0; d <= SRMECH_GENOME_MAX_GROUP_DEPTH; d++) {
        put_marker(b, &n, SRMECH_GENOME_GROUP_OPEN_MARKER, "d");
    }
    put_chrom(b, &n, "aa", 1u);
    for (uint32_t d = 0; d <= SRMECH_GENOME_MAX_GROUP_DEPTH; d++) {
        put_marker(b, &n, SRMECH_GENOME_GROUP_CLOSE_MARKER, NULL);
    }
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs) == SRMECH_ERR_LIMIT,
          "one past the cap is SRMECH_ERR_LIMIT, not SRMECH_ERR_OVERFLOW");
}

/* An UNGROUPED strand carries no frame markers, walks clean, and reports zero
 * groups — the "zero extra bytes" claim from the C side. */
static void test_ungrouped_is_unchanged(void)
{
    unsigned char b[MAXB * DIM];
    size_t n = 0u;
    uint32_t n_recs = 7u;
    printf("ungrouped\n");
    put_chrom(b, &n, "aa", 2u);
    put_chrom(b, &n, "bb", 2u);
    check(srmech_genome_group_walk(b, n, DIM, NULL, 0u, &n_recs) == SRMECH_OK,
          "an ungrouped strand walks clean");
    check(n_recs == 0u, "and reports zero groups");
}

/* Nesting: arity counts DIRECT members, and records come out innermost-first
 * because they are emitted on POP. */
static void test_nested(void)
{
    unsigned char inner[MAXB * DIM];
    unsigned char outer[MAXB * DIM];
    srmech_genome_group_t recs[8];
    size_t n_in = 0u, n_wrapped = 0u, n_out = 0u;
    uint32_t n_recs = 0u;
    printf("nesting\n");
    put_chrom(inner, &n_in, "aa", 1u);
    put_chrom(inner, &n_in, "bb", 1u);
    unsigned char wrapped[MAXB * DIM];
    srmech_status_t st = srmech_genome_group_wrap(
        inner, n_in, DIM, (const unsigned char *)"in", 2u,
        wrapped, sizeof(wrapped), &n_wrapped);
    check(st == SRMECH_OK, "inner wrap ok");
    st = srmech_genome_group_wrap(wrapped, n_wrapped, DIM,
                                  (const unsigned char *)"out", 3u,
                                  outer, sizeof(outer), &n_out);
    check(st == SRMECH_OK, "outer wrap ok");
    st = srmech_genome_group_walk(outer, n_out, DIM, recs, 8u, &n_recs);
    check(st == SRMECH_OK, "nested walk ok");
    check(n_recs == 2u, "two groups");
    check(strcmp(recs[0].label, "in") == 0,
          "records are emitted on POP, so the innermost closes first");
    check(recs[0].depth == 1u && recs[0].arity == 2u, "inner: depth 1, arity 2");
    check(recs[1].depth == 0u && recs[1].arity == 1u,
          "outer: depth 0, arity 1 — DIRECT members only");
}

int main(void)
{
    printf("srmech GROUP/v20 (rc442) — bare-C nesting grammar\n");
    test_wrap_then_walk();
    test_validate_only();
    test_arity();
    test_malformed();
    test_depth_limit();
    test_ungrouped_is_unchanged();
    test_nested();
    if (failures != 0) {
        printf("\n%d check(s) FAILED\n", failures);
        return 1;
    }
    printf("\nall checks passed\n");
    return 0;
}
