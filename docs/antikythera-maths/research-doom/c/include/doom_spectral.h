#ifndef DOOM_SPECTRAL_H
#define DOOM_SPECTRAL_H

#include <stdint.h>

/*
 * Spectral DOOM API
 * ALU-native operators for BIP kinematics and Graph-Laplacian physics.
 */

/* Standalone vs Engine boolean alignment */
#ifdef __DOOMTYPE__
#define d_boolean boolean
#define d_true true
#define d_false false
#else
typedef int d_boolean;
#define d_true 1
#define d_false 0
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

/* --- Physics (Z-Fiber) --- */

/* Returns true if an entity can transition between sectors based on Z constraints */
d_boolean ds_fiber_can_traverse(int sec_a, int sec_b, int32_t entity_z, int32_t entity_height);

/* --- Haptics (Tension) --- */

/* Returns the spectral tension [0.0, 1.0] for a hypervector relative to a sector anchor */
int32_t ds_get_haptic_tension(int sector_id, const ds_hypervector_t *h);

#endif /* DOOM_SPECTRAL_H */
