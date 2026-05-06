#ifndef DOOM_SPECTRAL_H
#define DOOM_SPECTRAL_H

#include <stdint.h>

/*
 * Spectral DOOM API
 * ALU-native operators for BIP kinematics and Graph-Laplacian physics.
 */

/* DOOM-native boolean support */
#ifndef __DOOMTYPE__
typedef enum { d_false, d_true } d_boolean;
#else
#define d_boolean boolean
#define d_true true
#define d_false false
#endif

#define DS_BIP_DIM 512
#define DS_MAX_SECTORS 256

/* --- Kinematics (BIP) --- */

typedef struct {
    int32_t x;     /* 16.16 fixed point */
    int32_t y;     /* 16.16 fixed point */
    uint32_t angle; /* 32-bit BAM */
} ds_kinematic_state_t;

typedef struct {
    int8_t h[DS_BIP_DIM]; /* Bipolar hypervector {-1, 1} */
} ds_hypervector_t;

/* Encodes a position into a BIP hypervector */
void ds_bip_encode(int32_t x, int32_t y, ds_hypervector_t *out);

/* Returns similarity [-1.0, 1.0] between two hypervectors (fixed-point return) */
int32_t ds_bip_similarity(const ds_hypervector_t *a, const ds_hypervector_t *b);

/* --- Topology (Sound Diffusion) --- */

typedef struct {
    float intensity[DS_MAX_SECTORS];
} ds_sound_field_t;

/* Diffuses sound across the sector graph */
void ds_diffuse_sound(int source_sector, float time, ds_sound_field_t *out);

/* Per-sector monster awareness from a diffused sound field, returned
 * as 16.16 fixed-point in [0, 1.0]. Caller MUST gate on a registered
 * spectral lattice (see ds_spectral_is_registered). */
int32_t ds_calculate_monster_awareness(int sector_id,
                                       const ds_sound_field_t *field);

/* --- Physics (Z-Fiber) --- */

/* Returns true if an entity can transition between sectors based on Z constraints */
d_boolean ds_fiber_can_traverse(int sec_a, int sec_b, int32_t entity_z, int32_t entity_height);

/* --- Physics (Sheaf Raycast) --- */

/* Bresenham line over the 128x128 MAPBLOCK grid. Currently a path-walk
 * stub that always returns d_true once the path is exhausted; the sheaf
 * restriction-map evaluation is reserved for a future track-3 ship.
 * Provided here so the p_sight.c integration site links cleanly. */
d_boolean ds_sheaf_raycast(int32_t x0, int32_t y0, int32_t x1, int32_t y1);

/* --- Haptics (Tension) --- */

/* Returns 16.16 fixed-point tension in [0, 1.0] = 1.0 - cosine_similarity
 * between the entity's current hypervector and the per-sector anchor.
 * Caller MUST gate this on a registered spectral lattice (E1M1 only at
 * present); on unregistered maps the call is undefined. */
int32_t ds_get_haptic_tension(int sector_id, const ds_hypervector_t *h);

/* --- Map gating ---
 *
 * Spectral lattice tables in ds_data.h are E1M1-specific (85 sectors,
 * precomputed phi/anchor/adjacency). The engine integration sites must
 * call ds_spectral_is_registered() before invoking any per-sector
 * predicate (ds_fiber_can_traverse, ds_get_haptic_tension); on
 * unregistered maps the predicates would assert and abort.
 *
 * Set by p_setup.c::P_SetupLevel after sectors are loaded; takes the
 * loaded sector count so a custom WAD with the same (episode, map)
 * but a different sector count won't accidentally register. */
void ds_set_current_map(int episode, int map, int sector_count);
d_boolean ds_spectral_is_registered(void);

/* --- Secret glow (IDSPECTRAL cheat) ---
 *
 * IDSPECTRAL toggle. When active, the engine (G_Ticker in g_game.c)
 * walks sectors with special == 9 and offsets their lightlevel by
 * ds_secretglow_pulse(sector_id, phase). Closer-in-spectral-phase
 * sectors pulse harder. The phase is driven by gametic (35 Hz) so the
 * hum cycles roughly every 1.8 s.
 *
 * The pulse math is a pure-ALU LUT lookup: cosine similarity between
 * the player's current BIP hypervector and the sector anchor is
 * combined with a quarter-wave sin LUT. No FPU, no allocations. */
void      ds_secretglow_set_active(d_boolean on);
d_boolean ds_secretglow_is_active(void);
int       ds_sin256(uint8_t phase);                   /* [-233..+233] */
int       ds_secretglow_pulse(int sector_id, uint8_t phase);

/* Returns 1 if sectors a and b are graph-adjacent in the precomputed
 * E1M1 spectral lattice (ds_e1m1_adj), 0 otherwise. Caller is
 * responsible for the registration check (ds_spectral_is_registered);
 * unregistered maps return 0 unconditionally. Used by g_game.c to
 * propagate the secret-glow pulse one hop along the spectral graph
 * so the hum is visible in sectors adjacent to a hidden secret. */
int       ds_lattice_adjacent(int a, int b);

#endif /* DOOM_SPECTRAL_H */
