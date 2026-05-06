#include "doom_spectral.h"
#include <stdio.h>
#include <assert.h>

void test_bip_c_port()
{
    ds_hypervector_t ha;
    ds_hypervector_t hb;
    ds_hypervector_t hc;
    int32_t sim_ab;
    int32_t sim_ac;

    /* Pos A: (100, 200) */
    ds_bip_encode(100 << 16, 200 << 16, &ha);
    /* Pos B: (101, 200) - Nearby */
    ds_bip_encode(101 << 16, 200 << 16, &hb);
    /* Pos C: (500, 800) - Far */
    ds_bip_encode(500 << 16, 800 << 16, &hc);

    sim_ab = ds_bip_similarity(&ha, &hb);
    sim_ac = ds_bip_similarity(&ha, &hc);

    printf("C Port BIP Test:\n");
    printf("  Similarity A-B (Adjacent): %.4f\n", (float)sim_ab / 65536.0f);
    printf("  Similarity A-C (Distant):  %.4f\n", (float)sim_ac / 65536.0f);
    
    assert(sim_ab > sim_ac);
}

int main()
{
    test_bip_c_port();
    return 0;
}
