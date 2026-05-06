#include "doom_spectral.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <getopt.h>

/* Headless DOOM engine mock for spectral verification */

static void print_help(const char *progname)
{
    printf("Usage: %s [options]\n", progname);
    printf("\nOptions:\n");
    printf("  -x, --pos-x <int>      Start X position (default: 1056)\n");
    printf("  -y, --pos-y <int>      Start Y position (default: -3616)\n");
    printf("  -t, --time <float>     Sound diffusion time (default: 0.8)\n");
    printf("  -s, --sector <int>     Source sector for sound (default: 0)\n");
    printf("  -h, --help             Display this help message\n");
    printf("\nSpectral DOOM Manifold Tools\n");
}

int main(int argc, char **argv)
{
    ds_hypervector_t h_start;
    ds_hypervector_t h_curr;
    int32_t start_x = 1056;
    int32_t start_y = -3616;
    float diffusion_time = 0.8f;
    int source_sector = 0;
    int i;

    static struct option long_options[] = {
        {"pos-x",  required_argument, 0, 'x'},
        {"pos-y",  required_argument, 0, 'y'},
        {"time",   required_argument, 0, 't'},
        {"sector", required_argument, 0, 's'},
        {"help",   no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    int opt;
    int option_index = 0;
    while ((opt = getopt_long(argc, argv, "x:y:t:s:h", long_options, &option_index)) != -1) {
        switch (opt) {
            case 'x': start_x = atoi(optarg); break;
            case 'y': start_y = atoi(optarg); break;
            case 't': diffusion_time = (float)atof(optarg); break;
            case 's': source_sector = atoi(optarg); break;
            case 'h': print_help(argv[0]); return 0;
            default: print_help(argv[0]); return 1;
        }
    }

    int32_t x_fixed = start_x * 65536;
    int32_t y_fixed = start_y * 65536;

    printf("--- Headless Spectral DOOM Runner ---\n");
    printf("Initializing E1M1 Hangar Manifold...\n\n");

    /* Initial State */
    ds_bip_encode(x_fixed, y_fixed, &h_start);
    printf("Initial Pos: (%d, %d)\n", start_x, start_y);
    printf("Initial BIP State (first 16 dims):\n  ");
    for (i = 0; i < 16; ++i) printf("%d ", h_start.h[i]);
    printf("\n\n");

    /* Simulate 5 ticks of movement (+64 units per tick in X) */
    int32_t curr_x = x_fixed;
    for (int t = 1; t <= 5; ++t)
    {
        curr_x += (64 * 65536);
        ds_bip_encode(curr_x, y_fixed, &h_curr);
        
        int32_t sim = ds_bip_similarity(&h_start, &h_curr);
        
        printf("Tick %d: Pos (%d, %d) | Similarity to Start: %.4f\n", 
               t, curr_x >> 16, start_y, (float)sim / 65536.0f);
    }

    printf("\n--- Test 2: Sound Diffusion ---\n");
    ds_sound_field_t field;
    printf("Source Sector: %d, Time: %.2f\n", source_sector, diffusion_time);
    ds_diffuse_sound(source_sector, diffusion_time, &field);
    printf("Sound Field (first 5 sectors):\n");
    for (i = 0; i < 5; ++i) {
        printf("  Sector %d: %.4f\n", i, field.intensity[i]);
    }

    return 0;
}
