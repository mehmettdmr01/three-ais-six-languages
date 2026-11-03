#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s N GENS SEED_FILE\n", argv[0]);
        return 1;
    }

    int N = atoi(argv[1]);
    int GENS = atoi(argv[2]);
    const char *filename = argv[3];

    FILE *f = fopen(filename, "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *file_buf = (char *)malloc(file_size + 1);
    if (!file_buf) {
        fclose(f);
        return 1;
    }
    size_t read_bytes = fread(file_buf, 1, file_size, f);
    fclose(f);
    file_buf[read_bytes] = '\0';

    int W = (N + 63) / 64;
    int rem = N % 64;
    uint64_t last_mask = (rem == 0) ? ~0ULL : ((1ULL << rem) - 1ULL);
    int last_bit_idx = (rem == 0) ? 63 : (rem - 1);

    uint64_t *cur = (uint64_t *)calloc((size_t)N * W, sizeof(uint64_t));
    uint64_t *nxt = (uint64_t *)calloc((size_t)N * W, sizeof(uint64_t));

    long file_pos = 0;
    for (int r = 0; r < N && file_pos < (long)read_bytes; r++) {
        int c = 0;
        while (c < N && file_pos < (long)read_bytes) {
            char ch = file_buf[file_pos++];
            if (ch == '1') {
                cur[r * W + (c / 64)] |= (1ULL << (c % 64));
                c++;
            } else if (ch == '0') {
                c++;
            }
        }
        while (file_pos < (long)read_bytes && (file_buf[file_pos] == '\r' || file_buf[file_pos] == '\n')) {
            file_pos++;
        }
    }
    free(file_buf);

    uint64_t *S1 = (uint64_t *)malloc(W * sizeof(uint64_t));
    uint64_t *C1 = (uint64_t *)malloc(W * sizeof(uint64_t));
    uint64_t *S1_L = (uint64_t *)malloc(W * sizeof(uint64_t));
    uint64_t *S1_R = (uint64_t *)malloc(W * sizeof(uint64_t));
    uint64_t *C1_L = (uint64_t *)malloc(W * sizeof(uint64_t));
    uint64_t *C1_R = (uint64_t *)malloc(W * sizeof(uint64_t));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (int g = 0; g < GENS; g++) {
        for (int r = 0; r < N; r++) {
            int r_up = (r == 0) ? (N - 1) : (r - 1);
            int r_dn = (r == N - 1) ? 0 : (r + 1);

            const uint64_t * __restrict__ row_u = &cur[r_up * W];
            const uint64_t * __restrict__ row_m = &cur[r * W];
            const uint64_t * __restrict__ row_d = &cur[r_dn * W];
            uint64_t * __restrict__ row_out = &nxt[r * W];

            for (int k = 0; k < W; k++) {
                uint64_t u = row_u[k];
                uint64_t m = row_m[k];
                uint64_t d = row_d[k];
                uint64_t u_xor_m = u ^ m;
                S1[k] = u_xor_m ^ d;
                C1[k] = (u & m) | (d & u_xor_m);
            }

            for (int k = 0; k < W; k++) {
                uint64_t L = S1[k] << 1;
                if (k > 0) L |= (S1[k - 1] >> 63) & 1ULL;
                else L |= (S1[W - 1] >> last_bit_idx) & 1ULL;
                if (k == W - 1) L &= last_mask;
                S1_L[k] = L;

                uint64_t R = S1[k] >> 1;
                if (k < W - 1) R |= (S1[k + 1] & 1ULL) << 63;
                else R |= (S1[0] & 1ULL) << last_bit_idx;
                if (k == W - 1) R &= last_mask;
                S1_R[k] = R;

                L = C1[k] << 1;
                if (k > 0) L |= (C1[k - 1] >> 63) & 1ULL;
                else L |= (C1[W - 1] >> last_bit_idx) & 1ULL;
                if (k == W - 1) L &= last_mask;
                C1_L[k] = L;

                R = C1[k] >> 1;
                if (k < W - 1) R |= (C1[k + 1] & 1ULL) << 63;
                else R |= (C1[0] & 1ULL) << last_bit_idx;
                if (k == W - 1) R &= last_mask;
                C1_R[k] = R;
            }

            for (int k = 0; k < W; k++) {
                uint64_t sL = S1_L[k], sC = S1[k], sR = S1_R[k];
                uint64_t cL = C1_L[k], cC = C1[k], cR = C1_R[k];

                uint64_t s_xor = sL ^ sC;
                uint64_t s_s = s_xor ^ sR;
                uint64_t c_s = (sL & sC) | (s_xor & sR);

                uint64_t c_xor = cL ^ cC;
                uint64_t s_c = c_xor ^ cR;
                uint64_t c_c = (cL & cC) | (c_xor & cR);

                uint64_t b0 = s_s;
                uint64_t b1 = s_c ^ c_s;
                uint64_t c_sc = s_c & c_s;
                uint64_t b2 = c_c ^ c_sc;
                uint64_t b3 = c_c & c_sc;

                uint64_t x = b0 & b1;
                uint64_t y = b0 | b1;
                uint64_t m = row_m[k];

                uint64_t res = (~b3) & ((x & ~b2) | (~y & b2 & m));
                if (k == W - 1) res &= last_mask;
                row_out[k] = res;
            }
        }
        uint64_t *tmp = cur;
        cur = nxt;
        nxt = tmp;
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed_ms = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1000000.0;
    long long sim_ms = (long long)llround(elapsed_ms);

    long long alive = 0;
    for (int i = 0; i < N * W; i++) {
        alive += __builtin_popcountll(cur[i]);
    }

    printf("alive=%lld sim_ms=%lld\n", alive, sim_ms);

    free(cur);
    free(nxt);
    free(S1);
    free(C1);
    free(S1_L);
    free(S1_R);
    free(C1_L);
    free(C1_R);

    return 0;
}
