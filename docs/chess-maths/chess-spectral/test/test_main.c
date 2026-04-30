/* test_main.c — test runner. Each test function returns 0 on success. */
#include <stdio.h>

int test_encoder(void);
int test_channels_extra(void);
int test_d4(void);
int test_temporal(void);
int test_gzip(void);
int test_frame_v5(void);

int main(void)
{
    int fails = 0;

    printf("[RUN ] test_encoder\n");
    if (test_encoder() != 0) { printf("[FAIL] test_encoder\n"); fails++; }
    else                     { printf("[ OK ] test_encoder\n"); }

    printf("[RUN ] test_channels_extra\n");
    if (test_channels_extra() != 0) { printf("[FAIL] test_channels_extra\n"); fails++; }
    else                            { printf("[ OK ] test_channels_extra\n"); }

    printf("[RUN ] test_d4\n");
    if (test_d4() != 0) { printf("[FAIL] test_d4\n"); fails++; }
    else                { printf("[ OK ] test_d4\n"); }

    printf("[RUN ] test_temporal\n");
    if (test_temporal() != 0) { printf("[FAIL] test_temporal\n"); fails++; }
    else                      { printf("[ OK ] test_temporal\n"); }

    printf("[RUN ] test_gzip\n");
    if (test_gzip() != 0) { printf("[FAIL] test_gzip\n"); fails++; }
    else                  { printf("[ OK ] test_gzip\n"); }

    printf("[RUN ] test_frame_v5\n");
    if (test_frame_v5() != 0) { printf("[FAIL] test_frame_v5\n"); fails++; }
    else                      { printf("[ OK ] test_frame_v5\n"); }

    if (fails == 0) {
        printf("\nALL TESTS PASSED\n");
        return 0;
    }
    printf("\n%d test(s) FAILED\n", fails);
    return 1;
}
