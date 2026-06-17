/* srmech_config.c — runtime, config-FILE-driven library limits (rc161).
 *
 * Compute-guard ceilings that used to be compiled-in `#define`s (e.g. the
 * Hermitian-eig node bound) become RUNTIME values read from a TOML config,
 * so a deployment tunes them with no recompile — "config-driven, not hard
 * coded" (user direction 2026-06-15). The first such value is
 * `[hermitian] max_nodes`; the registry is extensible to more keys.
 *
 * Sources, in honor with [[feedback_c_must_be_standalone_complete_no_python_fallback]]:
 *   - srmech_config_load_toml(bytes, len, ws, ws_len): parse a caller-held
 *     TOML blob (MCU-safe — a flash blob, no filesystem needed).
 *   - srmech_config_load_file(path, ws, ws_len): read the file through the
 *     PAL (srmech_plat_file_read — the single OS file surface) then parse.
 *     On a no-filesystem target the PAL returns SRMECH_ERR_IO and the caller
 *     uses the bytes form instead.
 * Both parse with the rc159 srmech_toml parser into the CALLER arena `ws`
 * (no malloc). Un-configured / missing keys keep the built-in default, so
 * the historical behaviour is preserved exactly until a config overrides it.
 *
 * The config is process-wide policy: set ONCE at startup (before concurrent
 * use), read-only thereafter. JPL Power-of-Ten clean (no goto, no malloc,
 * bounded, status returns, >=2 asserts / non-trivial fn).
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_platform.h"   /* srmech_plat_file_read (PAL file surface) */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* The live config. Default preserves the pre-rc161 ceiling (now overridable,
 * no longer a compiled-in cap). */
static uint32_t g_hermitian_max_nodes = SRMECH_HERMITIAN_DEFAULT_MAX_NODES;

uint32_t srmech_config_hermitian_max_nodes(void)
{
    assert(g_hermitian_max_nodes > 0u);
    assert(g_hermitian_max_nodes <= 0x7FFFFFFFu);
    return g_hermitian_max_nodes;
}

void srmech_config_reset_defaults(void)
{
    g_hermitian_max_nodes = SRMECH_HERMITIAN_DEFAULT_MAX_NODES;
    assert(g_hermitian_max_nodes > 0u);
    assert(SRMECH_HERMITIAN_DEFAULT_MAX_NODES > 0u);
}

/* Apply one parsed config tree into the live limits. Unknown / missing
 * sections + keys are left at their current value (partial config is OK). */
static void config_apply(const srmech_toml_value_t *root)
{
    assert(root != NULL);
    assert(root->type == SRMECH_TOML_TABLE);
    const srmech_toml_value_t *herm = srmech_toml_table_get(root, "hermitian");
    if (herm == NULL) { return; }
    const srmech_toml_value_t *mx = srmech_toml_table_get(herm, "max_nodes");
    if (mx != NULL && mx->type == SRMECH_TOML_INT
        && mx->u.i > 0 && mx->u.i <= 0x7FFFFFFF) {
        g_hermitian_max_nodes = (uint32_t)mx->u.i;
    }
}

srmech_status_t srmech_config_load_toml(const char *toml, size_t len,
                                        void *ws, size_t ws_len)
{
    assert(toml != NULL || len == 0);
    assert(ws != NULL || ws_len == 0);
    srmech_toml_value_t *root = NULL;
    srmech_status_t st = srmech_toml_parse(toml, len, ws, ws_len, &root);
    if (st != SRMECH_OK) {
        return st;
    }
    config_apply(root);
    return SRMECH_OK;
}

srmech_status_t srmech_config_load_file(const char *path,
                                        void *ws, size_t ws_len)
{
    assert(path != NULL);
    assert(ws != NULL || ws_len == 0);
    /* Carve the file-read buffer from the FRONT half of `ws`; the TOML parse
     * arena is the back half (the two never overlap — the parser copies its
     * strings into the parse arena, the source stays put). */
    size_t cap = ws_len / 2u;
    unsigned char *buf = (unsigned char *)ws;
    size_t got = 0u;
    srmech_status_t st = srmech_plat_file_read(path, buf, cap, &got);
    if (st != SRMECH_OK) {
        return st;
    }
    return srmech_config_load_toml((const char *)buf, got,
                                   buf + cap, ws_len - cap);
}
