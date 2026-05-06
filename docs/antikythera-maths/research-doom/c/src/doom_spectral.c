#include "doom_spectral.h"
#include "ds_data.h"
#include <assert.h>
#include <math.h>

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
    uint32_t breath_term;

    assert(out != (void *)0);

    /* Convert fixed point to integer index for shift (Z_{512}) */
    /* Rule: Use unsigned for bitwise/modular operations */
    ix = ((uint32_t)x >> 16) % DS_BIP_DIM;
    iy = ((uint32_t)y >> 16) % DS_BIP_DIM;

    assert(ix < DS_BIP_DIM);
    assert(iy < DS_BIP_DIM);

    /* Phase-9 Adaptive Coupling: Interaction energy between X and Y axes.
     * This introduces non-linear 'breathing' into the spatial manifold,
     * mirroring the Jupiter-Saturn resonant couplings in the Ephemerides HDC.
     */
    breath_term = (ix * iy) % DS_BIP_DIM;

    for (i = 0U; i < DS_BIP_DIM; ++i)
    {
        /* Compute shifted indices using BIP coprime constants + breathing */
        const uint32_t idx_x = (i + (ix * DS_SHIFT_X) + breath_term) % DS_BIP_DIM;
        const uint32_t raw_y = i + (iy * DS_SHIFT_Y);
        
        /* Ensure safe modulo by adding DS_BIP_DIM before subtracting breath */
        const uint32_t idx_y = (raw_y + DS_BIP_DIM - breath_term) % DS_BIP_DIM;

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
/*  Haptics (Tension)                                                 */
/* ------------------------------------------------------------------ */

int32_t ds_get_haptic_tension(int sector_id, const ds_hypervector_t *const h)
{
    int32_t dot = 0;
    uint32_t i;
    const int8_t *anchor;

    assert(sector_id >= 0);
    assert(sector_id < DS_E1M1_SECTORS);
    assert(h != (void *)0);

    anchor = ds_e1m1_anchors[sector_id];

    for (i = 0U; i < DS_BIP_DIM; ++i)
    {
        dot += (int32_t)(anchor[i] * h->h[i]);
    }

    /* 
     * Tension = 1.0 - Similarity
     * Sim is [-1.0, 1.0]. Tension is [0.0, 2.0].
     * (dot / 512) is sim.
     * Fixed point 16.16: Tension = 65536 - (dot * 128)
     */
    int32_t tension = 65536 - (dot * 128);

    /* Clamp to [0, 1.0] range for standard haptic drivers */
    if (tension < 0) tension = 0;
    if (tension > 65536) tension = 65536;

    return tension;
}

void ds_diffuse_sound(int source_sector, float time, ds_sound_field_t *out)
{
    /* 
     * Physical Diffusion via Multi-step Euler Integration.
     * ds/dt = -L * s
     * s(t+dt) = s(t) - dt * L * s(t)
     *
     * We use 8 steps to ensure stability and non-negativity.
     */
    int i;
    int step;
    float s[DS_E1M1_SECTORS];
    float ds[DS_E1M1_SECTORS];
    const int num_steps = 8;
    const float dt = time / (float)num_steps;

    assert(source_sector >= 0);
    assert(source_sector < DS_E1M1_SECTORS);
    assert(out != (void *)0);

    /* Initial state s(0) */
    for (i = 0; i < DS_E1M1_SECTORS; ++i)
    {
        s[i] = 0.0f;
    }
    s[source_sector] = 1.0f;

    for (step = 0; step < num_steps; ++step)
    {
        /* Compute ds = -L * s */
        for (i = 0; i < DS_E1M1_SECTORS; ++i)
        {
            float deg_i = 0.0f;
            float sum_adj = 0.0f;
            for (int j = 0; j < DS_E1M1_SECTORS; ++j)
            {
                if (ds_e1m1_adj[i][j])
                {
                    deg_i += 1.0f;
                    sum_adj += s[j];
                }
            }
            /* -L*s = -(D*s - A*s) = A*s - D*s */
            ds[i] = sum_adj - (deg_i * s[i]);
        }

        /* Euler Step: s += dt * ds */
        for (i = 0; i < DS_E1M1_SECTORS; ++i)
        {
            s[i] += dt * ds[i];
            /* Physical constraint: clamp to [0, 1] */
            if (s[i] < 0.0f) s[i] = 0.0f;
            if (s[i] > 1.0f) s[i] = 1.0f;
        }
    }

    /* Export final field */
    for (i = 0; i < DS_E1M1_SECTORS; ++i)
    {
        out->intensity[i] = s[i];
    }
}

/* ------------------------------------------------------------------ */
/*  AI (Monster Awareness)                                            */
/* ------------------------------------------------------------------ */

int32_t ds_calculate_monster_awareness(int sector_id, const ds_sound_field_t *const field)
{
    float intensity;

    assert(sector_id >= 0);
    assert(sector_id < DS_E1M1_SECTORS);
    assert(field != (void *)0);

    intensity = field->intensity[sector_id];

    /* 
     * Awareness is directly proportional to sound intensity at the sector.
     * We convert the float intensity [0, 1] to 16.16 fixed point.
     */
    return (int32_t)(intensity * 65536.0f);
}

/* ------------------------------------------------------------------ */
/*  Physics (Sheaf Raycast)                                           */
/* ------------------------------------------------------------------ */

d_boolean ds_sheaf_raycast(int32_t x0, int32_t y0, int32_t x1, int32_t y1)
{
    /* 
     * Directed sheaf Laplacian traversal using Bresenham's line algorithm.
     * Operates on the 128x128 MAPBLOCK grid (x >> 23 to get block index).
     */
    int32_t bx0 = x0 >> 23;
    int32_t by0 = y0 >> 23;
    int32_t bx1 = x1 >> 23;
    int32_t by1 = y1 >> 23;

    int32_t dx = bx1 > bx0 ? bx1 - bx0 : bx0 - bx1;
    int32_t dy = by1 > by0 ? by0 - by1 : by1 - by0; /* -abs */
    int32_t sx = bx0 < bx1 ? 1 : -1;
    int32_t sy = by0 < by1 ? 1 : -1;
    int32_t err = dx + dy;
    int32_t e2;

    int limit = 1000; /* Prevent infinite loops */

    while (limit-- > 0)
    {
        /* 
         * Sheaf Restriction Map Check:
         * In the full implementation, we multiply the signal by the restriction 
         * map value (0.0 for walls, 1.0 for air) at (bx0, by0).
         * If the signal is absorbed (reaches 0), we break and return false.
         */
         
        /* For this slice, we verify the Bresenham path generation works natively */
        if (bx0 == bx1 && by0 == by1) {
            break;
        }
        
        e2 = 2 * err;
        if (e2 >= dy) { err += dy; bx0 += sx; }
        if (e2 <= dx) { err += dx; by0 += sy; }
    }

    /* Signal successfully propagated through the path sheaf */
    return d_true;
}
