/*
 * srmech_bus.c — Cross-process IPC for srmech.bus (v0.5.0rc2; PAL'd v0.7.5rc5).
 *
 * The C peer for srmech.bus. Public symbols: the req/rep core
 * (srmech_bus_serve / srmech_bus_server_accept_one / srmech_bus_server_stop /
 *  srmech_bus_connect / srmech_bus_send_recv / srmech_bus_client_close) plus
 * one function-pointer typedef (srmech_bus_handler_callback_t), and — rc179
 * (ANNEX Batch A part 2) — the Bio-TOTP ENCRYPTED-transport variants
 * srmech_bus_serve_encrypted / srmech_bus_connect_encrypted (send_recv /
 * accept_one / stop / close are shared; they read the cipher state from the
 * handle). A bare-C host thus speaks the ENCRYPTED wire, not just plaintext.
 * The new symbols are additive, so SRMECH_ABI_VERSION stays 3.
 *
 * Transport (v0.7.5rc5): every OS call routes through the Platform
 * Abstraction Layer (srmech_platform.h / .c). This file carries ZERO
 * `#ifdef _WIN32` — it is the last raw-OS surface that became
 * platform-agnostic. The PAL maps the endpoint name to:
 *   POSIX  : AF_UNIX socket bound at ~/.srmech/bus-<name>.sock.
 *   Windows: named pipe at \\.\pipe\srmech-<name>.
 *
 * Framing: 4-byte big-endian length prefix + payload bytes (agnostic;
 * stays here). Handler dispatch: caller-provided function-pointer
 * callback (same pattern as v0.4.5rc8's srmech_cascade_chiral_dual_f64).
 * The Python ctypes layer wraps the typedef via ctypes.CFUNCTYPE.
 *
 * JPL Power-of-Ten discipline:
 *   - Rule 1 (no goto): clean control flow, early returns only.
 *   - Rule 3 (no malloc in hot path): the per-server workspace is
 *     allocated once at srmech_bus_serve entry and freed at
 *     srmech_bus_server_stop. The accept loop reuses the same
 *     workspace across all accepted connections.
 *   - Rule 4 (functions ≤ 60 lines): each public surface is split
 *     into small helpers.
 *   - Rule 5 (≥2 asserts per non-exempt function).
 *   - Rule 8 (no multi-line macros).
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_platform.h"

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 * Constants
 * ------------------------------------------------------------------ */

#define SRMECH_BUS_FRAME_PREFIX_BYTES 4u

/* Per-connection workspace size. Caller-supplied response buffer is
 * separate; this is the request-read buffer the accept loop owns. */
#define SRMECH_BUS_WORKSPACE_BYTES    (1u * 1024u * 1024u)   /* 1 MiB  */

/* ------------------------------------------------------------------ *
 * Bio-TOTP encrypted transport (rc179; ANNEX Batch A part 2).
 *
 * When an endpoint / client is opened via the *_encrypted variants, the
 * transport wraps the request/response payload in the rc178 UTLP Bio-TOTP
 * wire cipher (the DEFAULT stdlib HMAC-SHA-256 counter-mode path — the
 * AES-128-CTR `[crypto]` extra stays Python, out of the bare-C-host
 * default). Wire body = [nonce:16][ciphertext], TLV-framed as usual.
 * ENCRYPT composes srmech_bio_totp_derive_key + _keystream_xor; DECRYPT
 * composes srmech_bio_totp_decode_splice (permissive binding over the
 * OPAQUE payload — mirrors the pure decode_splice, NOT the Python bus's
 * strict JSON-Event binding + replay guard, which ride the JSON-Event C
 * surface tracked with pub/sub for rc180). Key window rolls on the PAL
 * wall clock (srmech_plat_now_ns); a large window_ns pins one key.
 * ------------------------------------------------------------------ */

/* dna copied onto the handle; matches srmech_bio_totp_derive_key's cap. */
#define SRMECH_BUS_CIPHER_MAX_DNA 256u
/* Bio-TOTP nonce width: sender_id_u64 || channel_id_u32 || packet_seq_u32. */
#define SRMECH_BUS_CIPHER_NONCE   16u
/* Caller-arena the decrypt hands srmech_bio_totp_decode_splice for its
 * binding-check srmech_json parse. Bounded; a plaintext whose would-be JSON
 * exceeds it overflows the parse -> permissive accept (correct for opaque
 * bytes). Comfortably binds typical small control frames. */
#define SRMECH_BUS_CIPHER_ARENA_BYTES (512u * 1024u)

/* Per-endpoint / per-connection cipher context. `enabled == 0` is the
 * plaintext path (rc6-compatible; zero cipher overhead). */
typedef struct srmech_bus_cipher {
    int      enabled;
    size_t   dna_len;
    uint8_t  dna[SRMECH_BUS_CIPHER_MAX_DNA];
    uint64_t sender_id;
    uint32_t channel_id;
    int64_t  window_ns;
    uint32_t send_seq;   /* monotone packet_seq (u32; wraps) — per-connection */
} srmech_bus_cipher_t;

/* ------------------------------------------------------------------ *
 * Opaque handle structs — the OS handle lives inside the PAL types.
 * ------------------------------------------------------------------ */

struct srmech_bus_server_handle {
    srmech_plat_stream_server_t      plat;     /* listener (PAL) */
    int                              stop_flag;
    srmech_bus_handler_callback_t    handler;
    void                            *user_data;
    uint8_t                         *workspace;
    /* response_buf is sized large enough for typical bus events.
     * Callers needing larger replies should split via streaming. */
    uint8_t                         *response_buf;
    size_t                           response_cap;
    /* Bio-TOTP transport config (cipher.enabled == 0 => plaintext). The
     * per-CONNECTION send_seq lives on a stack copy in the accept loop, so
     * two connections never share a nonce counter (this field is the seed). */
    srmech_bus_cipher_t              cipher;
    uint8_t                         *wire_buf;      /* encrypt/decrypt scratch */
    size_t                           wire_cap;
    uint8_t                         *decode_arena;  /* decode_splice bind arena */
    size_t                           decode_arena_cap;
};

struct srmech_bus_client_handle {
    srmech_plat_stream_conn_t        plat;     /* connection (PAL) */
    srmech_bus_cipher_t              cipher;
    uint8_t                         *wire_buf;
    size_t                           wire_cap;
    uint8_t                         *decode_arena;
    size_t                           decode_arena_cap;
};

/* ------------------------------------------------------------------ *
 * Framed I/O — 4-byte BE length prefix + payload (OS-agnostic)
 * ------------------------------------------------------------------ */

static void srmech_bus__write_u32_be(uint8_t out[4], uint32_t v)
{
    assert(out != NULL);
    out[0] = (uint8_t)((v >> 24) & 0xFFu);
    out[1] = (uint8_t)((v >> 16) & 0xFFu);
    out[2] = (uint8_t)((v >>  8) & 0xFFu);
    out[3] = (uint8_t)((v      ) & 0xFFu);
}

static uint32_t srmech_bus__read_u32_be(const uint8_t in[4])
{
    assert(in != NULL);
    uint32_t v = 0;
    v |= ((uint32_t)in[0]) << 24;
    v |= ((uint32_t)in[1]) << 16;
    v |= ((uint32_t)in[2]) <<  8;
    v |= ((uint32_t)in[3]);
    return v;
}

/* Write a full length-prefixed frame (4-byte BE prefix + body) to `conn`. */
static srmech_status_t srmech_bus__write_frame(
    srmech_plat_stream_conn_t *conn, const uint8_t *body, size_t len)
{
    assert(conn != NULL);
    assert(body != NULL || len == 0u);
    if (len > UINT32_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_bus__write_u32_be(prefix, (uint32_t)len);
    srmech_status_t rc = srmech_plat_stream_write_all(conn, prefix, sizeof prefix);
    if (rc != SRMECH_OK) {
        return rc;
    }
    return srmech_plat_stream_write_all(conn, body, len);
}

/* Read one length-prefixed frame body into `buf` (capacity `cap`); the body
 * length lands in *out_len. A body longer than `cap` is SRMECH_ERR_OVERFLOW. */
static srmech_status_t srmech_bus__read_frame(
    srmech_plat_stream_conn_t *conn, uint8_t *buf, size_t cap, size_t *out_len)
{
    assert(conn != NULL);
    assert(out_len != NULL);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_status_t rc = srmech_plat_stream_read_exact(conn, prefix, sizeof prefix);
    if (rc != SRMECH_OK) {
        return rc;   /* clean EOF or I/O error */
    }
    uint32_t plen = srmech_bus__read_u32_be(prefix);
    if (plen > cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_plat_stream_read_exact(conn, buf, plen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    *out_len = plen;
    return SRMECH_OK;
}

/* Assemble the 16-byte Bio-TOTP nonce ("Exon fields"), big-endian:
 * sender_id_u64 (8) || channel_id_u32 (4) || packet_seq_u32 (4). Byte-exact
 * with srmech.bus._bio_totp.build_nonce. */
static void srmech_bus__build_nonce(uint8_t out[SRMECH_BUS_CIPHER_NONCE],
                                    uint64_t sid, uint32_t cid, uint32_t seq)
{
    assert(out != NULL);
    assert(sizeof(uint64_t) == 8u);
    for (size_t i = 0; i < 8u; i++) {
        out[i] = (uint8_t)(sid >> (56u - (8u * i)));
    }
    out[8]  = (uint8_t)(cid >> 24);
    out[9]  = (uint8_t)(cid >> 16);
    out[10] = (uint8_t)(cid >>  8);
    out[11] = (uint8_t)(cid      );
    out[12] = (uint8_t)(seq >> 24);
    out[13] = (uint8_t)(seq >> 16);
    out[14] = (uint8_t)(seq >>  8);
    out[15] = (uint8_t)(seq      );
}

/* Encrypt `pt` into `out` = [nonce:16][ciphertext] (composes the rc178
 * srmech_bio_totp_derive_key + _keystream_xor). Advances c->send_seq (u32,
 * wraps). *out_len = 16 + pt_len. Byte-exact with BioTotpChannel.encrypt on
 * the DEFAULT HMAC-CTR path (time from the PAL wall clock). */
static srmech_status_t srmech_bus__encrypt(
    srmech_bus_cipher_t *c, const uint8_t *pt, size_t pt_len,
    uint8_t *out, size_t out_cap, size_t *out_len)
{
    assert(c != NULL);
    assert(out_len != NULL);
    if (out_cap < SRMECH_BUS_CIPHER_NONCE
        || pt_len > out_cap - SRMECH_BUS_CIPHER_NONCE) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_bus__build_nonce(out, c->sender_id, c->channel_id, c->send_seq);
    c->send_seq = (c->send_seq + 1u);   /* u32 wrap = Python (seq+1) & 0xffffffff */
    int64_t now_ns = 0;
    srmech_status_t rc = srmech_plat_now_ns(&now_ns);
    if (rc != SRMECH_OK) {
        return rc;
    }
    uint8_t key[SRMECH_BUS_CIPHER_NONCE];
    rc = srmech_bio_totp_derive_key(c->dna, c->dna_len, now_ns, c->window_ns, key);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_bio_totp_keystream_xor(key, out, pt, pt_len,
                                       out + SRMECH_BUS_CIPHER_NONCE);
    if (rc != SRMECH_OK) {
        return rc;
    }
    *out_len = SRMECH_BUS_CIPHER_NONCE + pt_len;
    return SRMECH_OK;
}

/* Decrypt a wire body `framed` = [nonce:16][ciphertext] into `out` (composes
 * the rc178 srmech_bio_totp_decode_splice — current window then ±1). Permissive
 * binding over the opaque payload; a body that fails all windows is
 * SRMECH_ERR_BAD_INPUT. *out_len = ciphertext length. */
static srmech_status_t srmech_bus__decrypt(
    srmech_bus_cipher_t *c, const uint8_t *framed, size_t framed_len,
    void *arena, size_t arena_cap, uint8_t *out, size_t out_cap, size_t *out_len)
{
    assert(c != NULL);
    assert(out_len != NULL);
    int64_t now_ns = 0;
    srmech_status_t rc = srmech_plat_now_ns(&now_ns);
    if (rc != SRMECH_OK) {
        return rc;
    }
    int64_t used_time = 0;
    int found = 0;
    rc = srmech_bio_totp_decode_splice(
        framed, framed_len, c->dna, c->dna_len, c->window_ns, now_ns,
        arena, arena_cap, out, out_cap, out_len, &used_time, &found);
    if (rc != SRMECH_OK) {
        return rc;
    }
    (void)used_time;
    if (!found) {
        return SRMECH_ERR_BAD_INPUT;   /* dna mismatch / skew > 1 window / tamper */
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Per-connection worker: read one request, dispatch, write reply.
 * Loops until peer closes. One implementation for every platform —
 * the connection is a PAL stream handle.
 * ------------------------------------------------------------------ */

static srmech_status_t srmech_bus__service_plain(
    srmech_bus_server_handle_t *h, srmech_plat_stream_conn_t *conn)
{
    assert(h != NULL);
    assert(conn != NULL);
    size_t plen = 0;
    srmech_status_t rc = srmech_bus__read_frame(
        conn, h->workspace, SRMECH_BUS_WORKSPACE_BYTES, &plen);
    if (rc != SRMECH_OK) {
        return rc;  /* clean EOF or I/O error */
    }
    size_t resp_len = h->response_cap;
    srmech_status_t hrc = h->handler(
        h->workspace, plen, h->response_buf, &resp_len, h->user_data);
    if (hrc != SRMECH_OK) {
        return hrc;
    }
    return srmech_bus__write_frame(conn, h->response_buf, resp_len);
}

/* Bio-TOTP encrypted request/response cycle (rc179). `cipher` carries the
 * per-connection send_seq for the server's response nonces. */
static srmech_status_t srmech_bus__service_encrypted(
    srmech_bus_server_handle_t *h, srmech_plat_stream_conn_t *conn,
    srmech_bus_cipher_t *cipher)
{
    assert(h != NULL);
    assert(cipher != NULL);
    size_t wlen = 0;
    srmech_status_t rc = srmech_bus__read_frame(
        conn, h->wire_buf, h->wire_cap, &wlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    size_t pt_len = 0;
    rc = srmech_bus__decrypt(cipher, h->wire_buf, wlen, h->decode_arena,
                             h->decode_arena_cap, h->workspace,
                             SRMECH_BUS_WORKSPACE_BYTES, &pt_len);
    if (rc != SRMECH_OK) {
        return rc;
    }
    size_t resp_len = h->response_cap;
    srmech_status_t hrc = h->handler(
        h->workspace, pt_len, h->response_buf, &resp_len, h->user_data);
    if (hrc != SRMECH_OK) {
        return hrc;
    }
    size_t out_wlen = 0;
    rc = srmech_bus__encrypt(cipher, h->response_buf, resp_len, h->wire_buf,
                             h->wire_cap, &out_wlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    return srmech_bus__write_frame(conn, h->wire_buf, out_wlen);
}

static void srmech_bus__connection_loop(
    srmech_bus_server_handle_t *h, srmech_plat_stream_conn_t *conn)
{
    assert(h != NULL);
    assert(conn != NULL);
    /* Per-connection cipher: copy the server config + reset the nonce counter
     * so two simultaneously-served connections never share a packet_seq. */
    srmech_bus_cipher_t conn_cipher = h->cipher;
    conn_cipher.send_seq = 0u;
    while (!h->stop_flag) {
        srmech_status_t rc = conn_cipher.enabled
            ? srmech_bus__service_encrypted(h, conn, &conn_cipher)
            : srmech_bus__service_plain(h, conn);
        if (rc != SRMECH_OK) {
            break;  /* peer closed or I/O error */
        }
    }
    (void)srmech_plat_stream_conn_close(conn);
}

/* ------------------------------------------------------------------ *
 * Public API
 * ------------------------------------------------------------------ */

/* Allocate the per-server handle + its workspace buffers.
 * Cold-path allocation (JPL Rule 3 — no allocation in hot path).
 * Returns NULL on allocation failure. */
static srmech_bus_server_handle_t *srmech_bus__alloc_server_handle(
    srmech_bus_handler_callback_t handler, void *user_data)
{
    assert(handler != NULL);
    srmech_bus_server_handle_t *h =
        (srmech_bus_server_handle_t *)calloc(
            1, sizeof(srmech_bus_server_handle_t));
    if (h == NULL) {
        return NULL;
    }
    assert(h != NULL);
    h->handler = handler;
    h->user_data = user_data;
    h->stop_flag = 0;
    h->workspace = (uint8_t *)malloc(SRMECH_BUS_WORKSPACE_BYTES);
    h->response_buf = (uint8_t *)malloc(SRMECH_BUS_WORKSPACE_BYTES);
    h->response_cap = SRMECH_BUS_WORKSPACE_BYTES;
    if (h->workspace == NULL || h->response_buf == NULL) {
        free(h->workspace);
        free(h->response_buf);
        free(h);
        return NULL;
    }
    return h;
}

static void srmech_bus__free_server_handle(srmech_bus_server_handle_t *h)
{
    assert(h != NULL);
    assert(h->workspace != NULL || h->response_buf != NULL);
    free(h->workspace);
    free(h->response_buf);
    free(h->wire_buf);       /* NULL on the plaintext path — free(NULL) is OK */
    free(h->decode_arena);
    free(h);
}

/* Copy + validate a caller DNA into a cipher context + allocate the encrypt/
 * decrypt wire scratch + the decode-splice bind arena. Cold path (JPL Rule 3).
 * SRMECH_ERR_BAD_INPUT for window_ns <= 0; SRMECH_ERR_OVERFLOW for
 * dna_len > SRMECH_BUS_CIPHER_MAX_DNA; SRMECH_ERR_INTERNAL on malloc failure. */
static srmech_status_t srmech_bus__cipher_setup(
    srmech_bus_cipher_t *cipher, uint8_t **wire_buf, size_t *wire_cap,
    uint8_t **decode_arena, size_t *decode_arena_cap,
    const uint8_t *dna, size_t dna_len, uint64_t sender_id,
    uint32_t channel_id, int64_t window_ns)
{
    assert(cipher != NULL);
    assert(wire_buf != NULL && decode_arena != NULL);
    if (window_ns <= 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (dna == NULL && dna_len != 0u) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dna_len > SRMECH_BUS_CIPHER_MAX_DNA) {
        return SRMECH_ERR_OVERFLOW;
    }
    memset(cipher, 0, sizeof *cipher);
    if (dna_len > 0u) {
        memcpy(cipher->dna, dna, dna_len);
    }
    cipher->enabled = 1;
    cipher->dna_len = dna_len;
    cipher->sender_id = sender_id;
    cipher->channel_id = channel_id;
    cipher->window_ns = window_ns;
    cipher->send_seq = 0u;
    const size_t wcap = SRMECH_BUS_WORKSPACE_BYTES + SRMECH_BUS_CIPHER_NONCE;
    uint8_t *wb = (uint8_t *)malloc(wcap);
    uint8_t *ar = (uint8_t *)malloc(SRMECH_BUS_CIPHER_ARENA_BYTES);
    if (wb == NULL || ar == NULL) {
        free(wb);
        free(ar);
        return SRMECH_ERR_INTERNAL;
    }
    *wire_buf = wb;
    *wire_cap = wcap;
    *decode_arena = ar;
    *decode_arena_cap = SRMECH_BUS_CIPHER_ARENA_BYTES;
    return SRMECH_OK;
}

srmech_status_t srmech_bus_serve(
    const char                       *name,
    srmech_bus_handler_callback_t     handler,
    void                             *user_data,
    srmech_bus_server_handle_t      **out_handle)
{
    if (name == NULL || handler == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(name != NULL);
    assert(handler != NULL);
    *out_handle = NULL;
    if (!srmech_plat_has_streams()) {
        return SRMECH_ERR_BAD_INPUT;  /* no IPC backend on this target */
    }
    srmech_bus_server_handle_t *h =
        srmech_bus__alloc_server_handle(handler, user_data);
    if (h == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_plat_stream_listen(name, &h->plat);
    if (rc != SRMECH_OK) {
        srmech_bus__free_server_handle(h);
        return rc;
    }
    *out_handle = h;
    return SRMECH_OK;
}

srmech_status_t srmech_bus_serve_encrypted(
    const char                       *name,
    srmech_bus_handler_callback_t     handler,
    void                             *user_data,
    const uint8_t                    *dna,
    size_t                            dna_len,
    uint64_t                          sender_id,
    uint32_t                          channel_id,
    int64_t                           window_ns,
    srmech_bus_server_handle_t      **out_handle)
{
    if (name == NULL || handler == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(name != NULL);
    assert(handler != NULL);
    *out_handle = NULL;
    if (!srmech_plat_has_streams()) {
        return SRMECH_ERR_BAD_INPUT;  /* no IPC backend on this target */
    }
    srmech_bus_server_handle_t *h =
        srmech_bus__alloc_server_handle(handler, user_data);
    if (h == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_bus__cipher_setup(
        &h->cipher, &h->wire_buf, &h->wire_cap, &h->decode_arena,
        &h->decode_arena_cap, dna, dna_len, sender_id, channel_id, window_ns);
    if (rc != SRMECH_OK) {
        srmech_bus__free_server_handle(h);
        return rc;
    }
    rc = srmech_plat_stream_listen(name, &h->plat);
    if (rc != SRMECH_OK) {
        srmech_bus__free_server_handle(h);
        return rc;
    }
    *out_handle = h;
    return SRMECH_OK;
}

srmech_status_t srmech_bus_server_accept_one(
    srmech_bus_server_handle_t *h)
{
    /* Blocking accept-one helper for tests / single-threaded harnesses.
     * Accepts ONE client, services its requests until peer closes, then
     * returns. Production callers typically spin this in a thread loop
     * (Python side handles thread-per-connection). */
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(h->handler != NULL);
    srmech_plat_stream_conn_t conn;
    srmech_status_t rc = srmech_plat_stream_accept(&h->plat, &conn);
    if (rc != SRMECH_OK) {
        return rc;
    }
    srmech_bus__connection_loop(h, &conn);
    return SRMECH_OK;
}

srmech_status_t srmech_bus_server_stop(srmech_bus_server_handle_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(h->workspace != NULL);
    h->stop_flag = 1;
    (void)srmech_plat_stream_server_close(&h->plat);
    free(h->workspace);
    free(h->response_buf);
    free(h->wire_buf);       /* NULL on the plaintext path — free(NULL) is OK */
    free(h->decode_arena);
    free(h);
    return SRMECH_OK;
}

srmech_status_t srmech_bus_connect(
    const char                       *name,
    srmech_bus_client_handle_t      **out_handle)
{
    if (name == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(name != NULL);
    assert(out_handle != NULL);
    *out_handle = NULL;
    if (!srmech_plat_has_streams()) {
        return SRMECH_ERR_BAD_INPUT;  /* no IPC backend on this target */
    }
    srmech_bus_client_handle_t *c =
        (srmech_bus_client_handle_t *)calloc(
            1, sizeof(srmech_bus_client_handle_t));
    if (c == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_plat_stream_connect(name, &c->plat);
    if (rc != SRMECH_OK) {
        free(c);
        return rc;
    }
    *out_handle = c;
    return SRMECH_OK;
}

srmech_status_t srmech_bus_connect_encrypted(
    const char                       *name,
    const uint8_t                    *dna,
    size_t                            dna_len,
    uint64_t                          sender_id,
    uint32_t                          channel_id,
    int64_t                           window_ns,
    srmech_bus_client_handle_t      **out_handle)
{
    if (name == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(name != NULL);
    assert(out_handle != NULL);
    *out_handle = NULL;
    if (!srmech_plat_has_streams()) {
        return SRMECH_ERR_BAD_INPUT;  /* no IPC backend on this target */
    }
    srmech_bus_client_handle_t *c =
        (srmech_bus_client_handle_t *)calloc(
            1, sizeof(srmech_bus_client_handle_t));
    if (c == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_bus__cipher_setup(
        &c->cipher, &c->wire_buf, &c->wire_cap, &c->decode_arena,
        &c->decode_arena_cap, dna, dna_len, sender_id, channel_id, window_ns);
    if (rc != SRMECH_OK) {
        free(c);
        return rc;
    }
    rc = srmech_plat_stream_connect(name, &c->plat);
    if (rc != SRMECH_OK) {
        free(c->wire_buf);
        free(c->decode_arena);
        free(c);
        return rc;
    }
    *out_handle = c;
    return SRMECH_OK;
}

/* Plaintext one-shot request/response (rc6 path). */
static srmech_status_t srmech_bus__send_recv_plain(
    srmech_bus_client_handle_t *h,
    const uint8_t *request, size_t request_len,
    uint8_t *response, size_t *response_len_inout)
{
    assert(h != NULL);
    assert(response_len_inout != NULL);
    srmech_status_t rc = srmech_bus__write_frame(
        &h->plat, request, request_len);
    if (rc != SRMECH_OK) {
        return rc;
    }
    size_t cap = *response_len_inout;
    return srmech_bus__read_frame(&h->plat, response, cap, response_len_inout);
}

/* Bio-TOTP encrypted one-shot request/response (rc179 path). */
static srmech_status_t srmech_bus__send_recv_encrypted(
    srmech_bus_client_handle_t *h,
    const uint8_t *request, size_t request_len,
    uint8_t *response, size_t *response_len_inout)
{
    assert(h != NULL);
    assert(response_len_inout != NULL);
    size_t wlen = 0;
    srmech_status_t rc = srmech_bus__encrypt(
        &h->cipher, request, request_len, h->wire_buf, h->wire_cap, &wlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_bus__write_frame(&h->plat, h->wire_buf, wlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    size_t rlen = 0;
    rc = srmech_bus__read_frame(&h->plat, h->wire_buf, h->wire_cap, &rlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    const size_t cap = *response_len_inout;
    size_t plen = 0;
    rc = srmech_bus__decrypt(&h->cipher, h->wire_buf, rlen, h->decode_arena,
                             h->decode_arena_cap, response, cap, &plen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    *response_len_inout = plen;
    return SRMECH_OK;
}

static srmech_status_t srmech_bus__send_recv(
    srmech_bus_client_handle_t *h,
    const uint8_t *request, size_t request_len,
    uint8_t *response, size_t *response_len_inout)
{
    assert(h != NULL);
    assert(response_len_inout != NULL);
    if (h->cipher.enabled) {
        return srmech_bus__send_recv_encrypted(
            h, request, request_len, response, response_len_inout);
    }
    return srmech_bus__send_recv_plain(
        h, request, request_len, response, response_len_inout);
}

srmech_status_t srmech_bus_send_recv(
    srmech_bus_client_handle_t       *h,
    const uint8_t                    *request, size_t request_len,
    uint8_t                          *response, size_t *response_len_inout)
{
    if (h == NULL || request == NULL || response == NULL
        || response_len_inout == NULL)
    {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(response_len_inout != NULL);
    if (request_len > UINT32_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    return srmech_bus__send_recv(
        h, request, request_len, response, response_len_inout);
}

srmech_status_t srmech_bus_client_close(srmech_bus_client_handle_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    srmech_status_t rc = srmech_plat_stream_conn_close(&h->plat);
    assert(rc == SRMECH_OK);
    (void)rc;
    free(h->wire_buf);       /* NULL on the plaintext path — free(NULL) is OK */
    free(h->decode_arena);
    free(h);
    return SRMECH_OK;
}
