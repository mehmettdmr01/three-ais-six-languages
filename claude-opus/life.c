// Conway's Game of Life on an N x N torus, bit-parallel: 64 cells per uint64_t.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef uint64_t u64;

// Horizontal 3-cell sum (left + self + right) of one row, as two bit planes.
static void hsum_row(const u64 *restrict r, u64 *restrict h0, u64 *restrict h1,
                     int W, int lastbit) {
    if (W == 1) {
        u64 c = r[0];
        u64 L = (c << 1) | ((c >> lastbit) & 1);
        u64 R = (c >> 1) | ((c & 1) << lastbit);
        u64 x = L ^ c;
        h0[0] = x ^ R;
        h1[0] = (L & c) | (x & R);
        return;
    }
    {
        u64 c = r[0];
        u64 L = (c << 1) | ((r[W - 1] >> lastbit) & 1);
        u64 R = (c >> 1) | (r[1] << 63);
        u64 x = L ^ c;
        h0[0] = x ^ R;
        h1[0] = (L & c) | (x & R);
    }
    for (int w = 1; w < W - 1; w++) {
        u64 c = r[w];
        u64 L = (c << 1) | (r[w - 1] >> 63);
        u64 R = (c >> 1) | (r[w + 1] << 63);
        u64 x = L ^ c;
        h0[w] = x ^ R;
        h1[w] = (L & c) | (x & R);
    }
    {
        u64 c = r[W - 1];
        u64 L = (c << 1) | (r[W - 2] >> 63);
        u64 R = (c >> 1) | ((r[0] & 1) << lastbit);
        u64 x = L ^ c;
        h0[W - 1] = x ^ R;
        h1[W - 1] = (L & c) | (x & R);
    }
}

// Next state of one row from the 3-cell sums of the rows above, at and below.
// Total of the 3x3 block (self included): alive next iff total == 3, or total == 4 and alive.
static void step_row(const u64 *restrict a0, const u64 *restrict a1,
                     const u64 *restrict b0, const u64 *restrict b1,
                     const u64 *restrict c0, const u64 *restrict c1,
                     const u64 *restrict cur, u64 *restrict out, int W) {
    for (int w = 0; w < W; w++) {
        u64 p = a0[w] ^ b0[w];
        u64 ones = p ^ c0[w];
        u64 carry = (a0[w] & b0[w]) | (p & c0[w]);
        u64 s = a1[w] ^ b1[w], sc = a1[w] & b1[w];
        u64 t = c1[w] ^ carry, tc = c1[w] & carry;
        u64 x = s ^ t;
        u64 eq3 = ones & x & ~(sc | tc);
        u64 eq4 = ~(ones | x) & ((s & t) | (sc ^ tc));
        out[w] = eq3 | (cur[w] & eq4);
    }
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s N GENS SEED_FILE\n", argv[0]);
        return 1;
    }
    int N = atoi(argv[1]);
    long gens = atol(argv[2]);
    FILE *f = fopen(argv[3], "rb");
    if (!f) {
        perror(argv[3]);
        return 1;
    }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc(sz + 1);
    sz = (long)fread(buf, 1, sz, f);
    fclose(f);

    int W = (N + 63) / 64;
    int lastbit = (N - 1) & 63;
    u64 lastmask = (N & 63) ? ((1ULL << (N & 63)) - 1) : ~0ULL;
    size_t cells = (size_t)N * W;
    u64 *g = calloc(cells, sizeof(u64));
    u64 *ng = calloc(cells, sizeof(u64));
    u64 *h0 = calloc(cells, sizeof(u64));
    u64 *h1 = calloc(cells, sizeof(u64));

    long k = 0, total = (long)N * N;
    for (long i = 0; i < sz && k < total; i++) {
        char ch = buf[i];
        if (ch == '0' || ch == '1') {
            if (ch == '1') {
                long y = k / N, x = k % N;
                g[y * W + x / 64] |= 1ULL << (x & 63);
            }
            k++;
        }
    }
    free(buf);

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long gen = 0; gen < gens; gen++) {
        for (int y = 0; y < N; y++)
            hsum_row(g + (size_t)y * W, h0 + (size_t)y * W, h1 + (size_t)y * W, W, lastbit);
        for (int y = 0; y < N; y++) {
            size_t up = (size_t)(y == 0 ? N - 1 : y - 1) * W;
            size_t mid = (size_t)y * W;
            size_t dn = (size_t)(y == N - 1 ? 0 : y + 1) * W;
            step_row(h0 + up, h1 + up, h0 + mid, h1 + mid, h0 + dn, h1 + dn,
                     g + mid, ng + mid, W);
            ng[mid + W - 1] &= lastmask;
        }
        u64 *tmp = g;
        g = ng;
        ng = tmp;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);

    long alive = 0;
    for (size_t i = 0; i < cells; i++) alive += __builtin_popcountll(g[i]);
    double ms = (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
    printf("alive=%ld sim_ms=%.3f\n", alive, ms);
    return 0;
}
