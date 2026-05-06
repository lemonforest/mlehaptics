#include "doom_spectral.h"
#include "ds_data.h"
#include <assert.h>

/* [SPECTRAL] Player BIP hypervector. Single global; written by
 * p_user.c once per think tick, read by ds_get_haptic_tension. */
ds_hypervector_t player_spectral_state;

/* 
 * JPL C Standard Compliance:
 * 1. No dynamic memory allocation.
 * 2. Fixed upper bounds for loops.
 * 3. High assertion density.
 * 4. Small, focused functions.
 */

#define DS_SHIFT_X 67U
#define DS_SHIFT_Y 7U

/* ------------------------------------------------------------------ */
/*  Kinematics (BIP)                                                  */
/* ------------------------------------------------------------------ */

void ds_bip_encode(const int32_t x, const int32_t y, ds_hypervector_t *const out)
{
    uint32_t i;
    uint32_t ix;
    uint32_t iy;

    assert(out != (void *)0);

    /* Convert fixed point to integer index for shift (Z_{512}) */
    /* Rule: Use unsigned for bitwise/modular operations */
    ix = ((uint32_t)x >> 16) % DS_BIP_DIM;
    iy = ((uint32_t)y >> 16) % DS_BIP_DIM;

    assert(ix < DS_BIP_DIM);
    assert(iy < DS_BIP_DIM);

    for (i = 0U; i < DS_BIP_DIM; ++i)
    {
        /* Compute shifted indices using BIP coprime constants */
        const uint32_t idx_x = (i + (ix * DS_SHIFT_X)) % DS_BIP_DIM;
        const uint32_t idx_y = (i + (iy * DS_SHIFT_Y)) % DS_BIP_DIM;

        assert(idx_x < DS_BIP_DIM);
        assert(idx_y < DS_BIP_DIM);

        /* Binding in bipolar space is multiplication */
        out->h[i] = ds_phi_x[idx_x] * ds_phi_y[idx_y];
    }
}

int32_t ds_bip_similarity(const ds_hypervector_t *const a, const ds_hypervector_t *const b)
{
    int32_t dot = 0;
    uint32_t i;

    assert(a != (void *)0);
    assert(b != (void *)0);

    for (i = 0U; i < DS_BIP_DIM; ++i)
    {
        dot += (int32_t)(a->h[i] * b->h[i]);
    }

    /* Return similarity as 16.16 fixed point [-1.0, 1.0] */
    /* (dot / 512) * 65536 = dot * 128 */
    return dot * 128;
}

/* ------------------------------------------------------------------ */
/*  Physics (Z-Fiber)                                                 */
/* ------------------------------------------------------------------ */

d_boolean ds_fiber_can_traverse(const int sec_a, const int sec_b,
                           const int32_t entity_z, const int32_t entity_height)
{
    const ds_sector_info_t *s_b;
    const int32_t z = entity_z >> 16;
    const int32_t h = entity_height >> 16;
    const int32_t max_step = 24;

    assert(sec_a >= 0);
    assert(sec_a < DS_E1M1_SECTORS);
    assert(sec_b >= 0);
    assert(sec_b < DS_E1M1_SECTORS);
    assert(h > 0);

    /* Intra-sector movement is not a Z-fiber transition; let it
     * through unconditionally. (P_CheckPosition fires this gate every
     * step, including the overwhelming majority of steps that stay
     * inside the same sector. ds_e1m1_adj is a strict adjacency
     * matrix with zero diagonal -- without this short-circuit, every
     * intra-sector movement reads adj[i][i]==0 and gets blocked,
     * trapping the player in their spawn cell. The Z-fiber check
     * still applies to inter-sector transitions below.) */
    if (sec_a == sec_b)
    {
        return d_true;
    }

    /* If not adjacent in the manifold, cannot traverse */
    if (ds_e1m1_adj[sec_a][sec_b] == 0)
    {
        return d_false;
    }

    s_b = &ds_e1m1_sectors[sec_b];

    /* Z-Fiber Constraints:
     * 1. Floor of B must be reachable with a 24-unit step.
     * 2. Ceiling of B must be higher than the entity's top.
     */
    if (s_b->floor > (z + max_step))
    {
        return d_false;
    }

    if (s_b->ceiling < (z + h))
    {
        return d_false;
    }

    return d_true;
}

/* ------------------------------------------------------------------ */
/*  Topology (Sound Diffusion)                                         */
/* ------------------------------------------------------------------ */

void ds_diffuse_sound(int source_sector, float time, ds_sound_field_t *out)
{
    /* 
     * Simplified spectral diffusion for the C port.
     * In a full implementation, this would use the Laplacian and matrix exp.
     * For the 'slice', we'll use a single-step adjacency prop as a proxy.
     */
    int i;

    assert(source_sector >= 0);
    assert(source_sector < DS_E1M1_SECTORS);
    assert(out != (void *)0);

    for (i = 0; i < DS_E1M1_SECTORS; ++i)
    {
        out->intensity[i] = 0.0f;
    }

    out->intensity[source_sector] = 1.0f;

    /* Single-step propagation (approx t=1.0) */
    if (time > 0.0f)
    {
        for (i = 0; i < DS_E1M1_SECTORS; ++i)
        {
            if (ds_e1m1_adj[source_sector][i] > 0)
            {
                out->intensity[i] = 0.5f;
            }
        }
    }
}

/* ------------------------------------------------------------------ */
/*  AI (Monster awareness)                                             */
/* ------------------------------------------------------------------ */

int32_t ds_calculate_monster_awareness(const int sector_id,
                                       const ds_sound_field_t *const field)
{
    float intensity;

    assert(sector_id >= 0);
    assert(sector_id < DS_E1M1_SECTORS);
    assert(field != (void *)0);

    intensity = field->intensity[sector_id];
    /* Intensity in [0, 1] -> 16.16 fixed point. */
    return (int32_t)(intensity * 65536.0f);
}

/* ------------------------------------------------------------------ */
/*  Haptics (Tension)                                                 */
/* ------------------------------------------------------------------ */

int32_t ds_get_haptic_tension(const int sector_id, const ds_hypervector_t *const h)
{
    int32_t dot = 0;
    uint32_t i;
    const int8_t *anchor;
    int32_t tension;

    assert(sector_id >= 0);
    assert(sector_id < DS_E1M1_SECTORS);
    assert(h != (void *)0);

    anchor = ds_e1m1_anchors[sector_id];

    for (i = 0U; i < DS_BIP_DIM; ++i)
    {
        dot += (int32_t)(anchor[i] * h->h[i]);
    }

    /* Tension = 1.0 - similarity, in 16.16 fixed point.
     * similarity = dot / DS_BIP_DIM (range [-1, +1])
     * (dot / 512) * 65536 = dot * 128, so tension = 65536 - dot * 128. */
    tension = 65536 - (dot * 128);
    if (tension < 0)      tension = 0;
    if (tension > 65536)  tension = 65536;
    return tension;
}

/* ------------------------------------------------------------------ */
/*  Physics (Sheaf Raycast)                                            */
/* ------------------------------------------------------------------ */

d_boolean ds_sheaf_raycast(const int32_t x0, const int32_t y0,
                           const int32_t x1, const int32_t y1)
{
    /* Bresenham over the 128x128 MAPBLOCK grid (>>23 from 16.16 fixed
     * world coords; one block = 128 fracunits = 128 * 65536 raw units).
     *
     * Track 3 (Dynamic Sheaf Laplacian) restriction-map evaluation is
     * deferred — for now we walk the path and return d_true so the
     * p_sight.c fast-path is a no-op rather than a false-negative. */
    int32_t bx0 = x0 >> 23;
    int32_t by0 = y0 >> 23;
    const int32_t bx1 = x1 >> 23;
    const int32_t by1 = y1 >> 23;

    const int32_t dx = (bx1 > bx0) ? (bx1 - bx0) : (bx0 - bx1);
    /* Standard Bresenham wants dy = -|by1 - by0|. The reference
     * implementation had a sign bug here: negation was applied to only
     * one branch. Compute |dy| then negate once. */
    const int32_t abs_dy = (by1 > by0) ? (by1 - by0) : (by0 - by1);
    const int32_t dy = -abs_dy;
    const int32_t sx = (bx0 < bx1) ? 1 : -1;
    const int32_t sy = (by0 < by1) ? 1 : -1;
    int32_t err = dx + dy;
    int32_t e2;
    int limit = 1000;  /* upper bound: blockmap diagonal ~360 blocks max */

    while (limit-- > 0)
    {
        if (bx0 == bx1 && by0 == by1)
        {
            break;
        }
        e2 = 2 * err;
        if (e2 >= dy) { err += dy; bx0 += sx; }
        if (e2 <= dx) { err += dx; by0 += sy; }
    }

    return d_true;
}

/* ------------------------------------------------------------------ */
/*  Map gating                                                         */
/* ------------------------------------------------------------------ */

/* The spectral lattice tables in ds_data.h are E1M1-specific. On any
 * other map the per-sector predicates would assert and abort. Engine
 * integration sites MUST gate calls on ds_spectral_is_registered(). */
static d_boolean ds_lattice_registered = d_false;

void ds_set_current_map(const int episode, const int map,
                        const int sector_count)
{
    /* Only E1M1 from the stock IWAD ships with a precomputed lattice.
     * A custom WAD using the same (episode, map) tag but a different
     * sector count would index the per-sector tables out of range, so
     * the size match is part of the registration contract. */
    ds_lattice_registered =
        (episode == 1 && map == 1 && sector_count == DS_E1M1_SECTORS)
        ? d_true : d_false;
}

d_boolean ds_spectral_is_registered(void)
{
    return ds_lattice_registered;
}

int ds_lattice_adjacent(const int a, const int b)
{
    if (!ds_lattice_registered) return 0;
    if (a < 0 || a >= DS_E1M1_SECTORS) return 0;
    if (b < 0 || b >= DS_E1M1_SECTORS) return 0;
    return ds_e1m1_adj[a][b] ? 1 : 0;
}

/* ------------------------------------------------------------------ */
/*  Secret glow (IDSPECTRAL cheat) -- spectral math primitives        */
/* ------------------------------------------------------------------ */

/* The per-tic sector walk lives in g_game.c (which has direct access
 * to sector_t via the full engine header chain). doom_spectral.c
 * exports only the spectral math primitives so this module stays
 * self-contained and JPL-disciplined. */

static d_boolean ds_secretglow_active = d_false;

void ds_secretglow_set_active(const d_boolean on)
{
    ds_secretglow_active = on;
}

d_boolean ds_secretglow_is_active(void)
{
    return ds_secretglow_active;
}

/* Quarter-wave sin LUT in 16.8 fixed point (Q8); pure ALU. The full
 * cycle is 256 phase units; at 35 Hz with phase += 4 per tic, that's
 * one full pulse every ~1.83 s. Range: [-233..+233]. */
static const int16_t ds_sine256_quarter[65] = {
    0,    6,   13,   19,   25,   31,   37,   44,   50,   56,
   62,   68,   74,   80,   86,   92,   98,  104,  109,  115,
  121,  126,  132,  137,  142,  147,  152,  157,  162,  167,
  171,  176,  180,  184,  188,  192,  196,  199,  203,  206,
  209,  212,  214,  217,  219,  221,  223,  225,  227,  228,
  229,  230,  231,  232,  232,  233,  233,  233,  233,  233,
  233,  232,  232,  231,  230
};
int ds_sin256(uint8_t phase)
{
    uint8_t q = phase >> 6;
    uint8_t i = phase & 0x3f;
    if (q == 0)        return  ds_sine256_quarter[i];
    else if (q == 1)   return  ds_sine256_quarter[64 - i];
    else if (q == 2)   return -ds_sine256_quarter[i];
    else               return -ds_sine256_quarter[64 - i];
}

/* Per-secret-sector lightlevel pulse delta. Caller passes the sector
 * index and the tic-driven phase; returns a signed lightlevel offset.
 *
 * Composition:
 *   baseline_hum_amplitude     = 32 lightlevel units (always present)
 *   similarity_gain            = up to +64 units at peak spectral
 *                                 similarity to player's BIP HV
 *   sin envelope               = quarter-wave LUT, [-233..+233] in Q8
 *
 * Total swing peaks at roughly +/- 90 units around baseline -- a
 * full third of the 0..255 lightlevel range, unmistakable to the eye.
 * Still pure-ALU: one tension call, one LUT lookup, three shifts. */
int ds_secretglow_pulse(int sector_id, uint8_t phase)
{
    int32_t tension;
    int32_t cos_sim_q16;
    int32_t similarity_scaled;
    int     sin_val;

    if (sector_id < 0 || sector_id >= DS_E1M1_SECTORS)
    {
        /* No anchor for this sector -- still hum the baseline so
         * non-E1M1 secrets show some life if a future ds_data lattice
         * lands. */
        sin_val = ds_sin256(phase);
        return (32 * sin_val) >> 8;  /* +/- ~29 units */
    }

    tension = ds_get_haptic_tension(sector_id, &player_spectral_state);
    cos_sim_q16 = 65536 - tension;
    if (cos_sim_q16 < 0) cos_sim_q16 = 0;

    /* Map cos similarity [0..65536] -> [0..64] gain. Pure shifts. */
    similarity_scaled = cos_sim_q16 >> 10;
    if (similarity_scaled > 64) similarity_scaled = 64;

    sin_val = ds_sin256(phase);  /* [-233..+233] */
    /* baseline 32 units + up to 64 more from similarity. */
    return ((similarity_scaled + 32) * sin_val) >> 8;
}
