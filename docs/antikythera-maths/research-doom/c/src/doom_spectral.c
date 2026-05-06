#include "doom_spectral.h"
#include "ds_data.h"
#include <assert.h>

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

bool ds_fiber_can_traverse(const int sec_a, const int sec_b, 
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
        return false;
    }

    s_b = &ds_e1m1_sectors[sec_b];

    /* Z-Fiber Constraints:
     * 1. Floor of B must be reachable with a 24-unit step.
     * 2. Ceiling of B must be higher than the entity's top.
     */
    if (s_b->floor > (z + max_step))
    {
        return false;
    }

    if (s_b->ceiling < (z + h))
    {
        return false;
    }

    return true;
}

/* ------------------------------------------------------------------ */
/*  Topology (Sound Diffusion)                                         */
/* ------------------------------------------------------------------ */

void ds_diffuse_sound(int source_sector, float time, ds_sound_field_t *out)
{
    /* 
     * Full spectral diffusion using Taylor series expansion of e^-Lt:
     * s(t) = (I - Lt + (Lt)^2/2! - (Lt)^3/3!) * s(0)
     *
     * We perform 3 iterations (up to cubic term) for high-fidelity 
     * topological flooding.
     */
    int i;
    int k;
    float temp[DS_E1M1_SECTORS];
    float s_prev[DS_E1M1_SECTORS];
    const float dt = time;

    assert(source_sector >= 0);
    assert(source_sector < DS_E1M1_SECTORS);
    assert(out != (void *)0);

    /* Initial state s(0) */
    for (i = 0; i < DS_E1M1_SECTORS; ++i)
    {
        out->intensity[i] = 0.0f;
        s_prev[i] = 0.0f;
    }
    out->intensity[source_sector] = 1.0f;
    s_prev[source_sector] = 1.0f;

    /* Iteration 1: -Lt * s(0) */
    /* Iteration 2: (Lt)^2/2 * s(0) ... etc */
    /* We use the adjacency matrix to compute L*s since L = D - A */

    for (k = 1; k <= 3; ++k)
    {
        float factorial = 1.0f;
        for (i = 1; i <= k; ++i) factorial *= (float)i;

        /* temp = L * s_prev */
        for (i = 0; i < DS_E1M1_SECTORS; ++i)
        {
            float deg_i = 0.0f;
            float sum_adj = 0.0f;
            for (int j = 0; j < DS_E1M1_SECTORS; ++j)
            {
                if (ds_e1m1_adj[i][j])
                {
                    deg_i += 1.0f;
                    sum_adj += s_prev[j];
                }
            }
            /* L * s = (D - A) * s = D*s - A*s */
            temp[i] = (deg_i * s_prev[i]) - sum_adj;
        }

        /* update out: s(t) += ((-t)^k / k!) * (L^k * s0) */
        float coeff = powf(-dt, (float)k) / factorial;
        for (i = 0; i < DS_E1M1_SECTORS; ++i)
        {
            out->intensity[i] += coeff * temp[i];
            s_prev[i] = temp[i]; /* for next power of L */
        }
    }
}

}
