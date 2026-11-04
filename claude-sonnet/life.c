#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
typedef uint64_t u64;
int main(int argc, char **argv) {
    if (argc < 4) return 1;
    long N = atol(argv[1]), G = atol(argv[2]);
    FILE *f = fopen(argv[3], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char *buf = malloc(sz + 1);
    sz = fread(buf, 1, sz, f); fclose(f);
    long W = (N + 63) / 64, L = N - 64 * (W - 1);
    u64 lm = L == 64 ? ~0ULL : ((1ULL << L) - 1);
    u64 *cur = calloc(N * W, 8), *nxt = calloc(N * W, 8);
    u64 *we = calloc(N * W, 8), *ee = calloc(N * W, 8);
    long k = 0, tot = N * N;
    for (long i = 0; i < sz && k < tot; i++) {
        if (buf[i] == '1') { cur[(k / N) * W + (k % N) / 64] |= 1ULL << ((k % N) % 64); k++; }
        else if (buf[i] == '0') k++;
    }
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long g = 0; g < G; g++) {
        for (long r = 0; r < N; r++) {
            const u64 *row = cur + r * W; u64 *wr = we + r * W, *er = ee + r * W;
            for (long i = 0; i < W; i++) {
                u64 x = row[i], e, w;
                if (i < W - 1) e = (x >> 1) | (row[i + 1] << 63);
                else e = (x >> 1) | ((row[0] & 1) << (L - 1));
                if (i > 0) w = (x << 1) | (row[i - 1] >> 63);
                else w = (x << 1) | ((row[W - 1] >> (L - 1)) & 1);
                if (i == W - 1) w &= lm;
                wr[i] = w; er[i] = e;
            }
        }
        for (long r = 0; r < N; r++) {
            long ru = (r == 0 ? N - 1 : r - 1), rd = (r == N - 1 ? 0 : r + 1);
            const u64 *uw = we + ru * W, *ue = ee + ru * W, *uc = cur + ru * W;
            const u64 *mw = we + r * W, *me = ee + r * W, *mc = cur + r * W;
            const u64 *dw = we + rd * W, *de = ee + rd * W, *dc = cur + rd * W;
            u64 *o = nxt + r * W;
            for (long i = 0; i < W; i++) {
                u64 a = uw[i], b = uc[i], c = ue[i];
                u64 s1 = a ^ b ^ c, c1 = (a & b) | (c & (a ^ b));
                u64 d = mw[i], e = me[i];
                u64 s2 = d ^ e, c2 = d & e;
                a = dw[i]; b = dc[i]; c = de[i];
                u64 s3 = a ^ b ^ c, c3 = (a & b) | (c & (a ^ b));
                u64 on = s1 ^ s2 ^ s3;
                u64 k1 = (s1 & s2) | (s3 & (s1 ^ s2));
                u64 par = c1 ^ c2 ^ c3 ^ k1;
                u64 two = (c1 & c2) | (c3 & k1) | ((c1 | c2) & (c3 | k1));
                o[i] = par & ~two & (on | mc[i]);
            }
        }
        u64 *t = cur; cur = nxt; nxt = t;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    long alive = 0;
    for (long i = 0; i < N * W; i++) alive += __builtin_popcountll(cur[i]);
    double ms = (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
    printf("alive=%ld sim_ms=%.3f\n", alive, ms);
    return 0;
}
