/* test_srmech_config.c — rc161 config layer + PAL file surface smoke test.
 *
 * Proves the Hermitian-eig ceiling is CONFIG-DRIVEN (a TOML value, not a
 * compiled-in #define): default 2048, overridable via a TOML blob AND via a
 * file read THROUGH THE PAL (srmech_plat_file_write/_read). Standalone — no
 * Python. License: MIT.
 */
#include "srmech.h"
#include "srmech_platform.h"

#include <stdio.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *desc)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", desc); }
    else      { g_fail++; printf("  FAIL  %s\n", desc); }
}

int main(void)
{
    printf("== srmech_config smoke tests ==\n");
    static unsigned char ws[1 << 16];

    /* Default ceiling (config-driven, built-in default 2048). */
    srmech_config_reset_defaults();
    check(srmech_config_hermitian_max_nodes() == SRMECH_HERMITIAN_DEFAULT_MAX_NODES,
          "default hermitian max_nodes == built-in default (2048)");

    /* Override DOWN via a TOML blob. */
    const char *toml_lo = "[hermitian]\nmax_nodes = 512\n";
    srmech_status_t st = srmech_config_load_toml(toml_lo, strlen(toml_lo),
                                                 ws, sizeof(ws));
    check(st == SRMECH_OK, "load_toml (max_nodes = 512) OK");
    check(srmech_config_hermitian_max_nodes() == 512u,
          "ceiling lowered to 512 by config");

    /* Override UP past the old 2048 (proves it is no longer a hard cap). */
    const char *toml_hi = "[hermitian]\nmax_nodes = 5000\n";
    st = srmech_config_load_toml(toml_hi, strlen(toml_hi), ws, sizeof(ws));
    check(st == SRMECH_OK, "load_toml (max_nodes = 5000) OK");
    check(srmech_config_hermitian_max_nodes() == 5000u,
          "ceiling raised to 5000 (the old 2048 was not a hard cap)");

    /* Partial / unrelated config leaves the value unchanged. */
    const char *toml_other = "[unrelated]\nfoo = 1\n";
    st = srmech_config_load_toml(toml_other, strlen(toml_other), ws, sizeof(ws));
    check(st == SRMECH_OK && srmech_config_hermitian_max_nodes() == 5000u,
          "unrelated config keeps the current value (partial config OK)");

    /* Reset to default. */
    srmech_config_reset_defaults();
    check(srmech_config_hermitian_max_nodes() == 2048u, "reset_defaults restores 2048");

    /* FILE path THROUGH THE PAL: write a config file, then load_file it. */
    check(srmech_plat_has_filesystem() == 1, "PAL reports a filesystem (host)");
    const char *path = "/tmp/srmech_test_limits.toml";
    const char *body = "[hermitian]\nmax_nodes = 777\n";
    st = srmech_plat_file_write(path, 0, (const unsigned char *)body, strlen(body));
    check(st == SRMECH_OK, "PAL file_write the config file");
    st = srmech_config_load_file(path, ws, sizeof(ws));
    check(st == SRMECH_OK, "config_load_file (via PAL read) OK");
    check(srmech_config_hermitian_max_nodes() == 777u,
          "ceiling set to 777 from the TOML FILE through the PAL");

    /* PAL read round-trips the bytes. */
    static unsigned char rb[256];
    size_t got = 0;
    st = srmech_plat_file_read(path, rb, sizeof(rb), &got);
    check(st == SRMECH_OK && got == strlen(body)
          && memcmp(rb, body, got) == 0, "PAL file_read round-trips the bytes");

    /* A missing file is a clean SRMECH_ERR_IO (not a crash). */
    st = srmech_config_load_file("/tmp/srmech_does_not_exist_zzz.toml", ws, sizeof(ws));
    check(st == SRMECH_ERR_IO, "load_file on a missing file -> SRMECH_ERR_IO");

    srmech_config_reset_defaults();
    printf("== %d passed, %d failed ==\n", g_pass, g_fail);
    return (g_fail == 0) ? 0 : 1;
}
