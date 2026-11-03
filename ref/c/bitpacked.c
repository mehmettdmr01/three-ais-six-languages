/* "Not a paradigm, a data layout": the same C, but one cell is one bit.
   Each row is N/64 64-bit words; 64 cells advance with one word operation.
   Neighbour counts come from bit-sliced adders (half/full adder logic).
   Wrapping edges: carry across words when shifting, modulo on rows. */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

typedef uint64_t u64;
static int N, W, GENS;   /* W = N/64 words per row */

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static void read_seed(const char *path, u64 *g) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); exit(1); }
    size_t len = (size_t)(N + 1) * N;
    char *t = malloc(len);
    len = fread(t, 1, len, f);
    fclose(f);
    size_t j = 0;
    for (size_t i = 0; i < len; i++) if (t[i] != '\n') {
        if (t[i] == '1') g[j / N * W + (j % N) / 64] |= (u64)1 << ((j % N) % 64);
        j++;
    }
    free(t);
}

/* west (x-1) and east (x+1) neighbour bits of a row, wrapping */
static inline u64 west(const u64 *r, int i) { return (r[i] << 1) | (r[(i + W - 1) % W] >> 63); }
static inline u64 east(const u64 *r, int i) { return (r[i] >> 1) | (r[(i + 1) % W] << 63); }

/* full adder: add three bit vectors -> (s0: ones, s1: twos) */
#define ADD3(a, b, c, s0, s1) do { u64 _x = (a) ^ (b); s0 = _x ^ (c); s1 = ((a) & (b)) | (_x & (c)); } while (0)

static void step(const u64 *cur, u64 *next) {
    for (int y = 0; y < N; y++) {
        const u64 *up = cur + ((y + N - 1) % N) * W, *me = cur + y * W, *dn = cur + ((y + 1) % N) * W;
        for (int i = 0; i < W; i++) {
            u64 u0, u1, d0, d1, m0, m1, t0, c1, p1, p2, t1, c2, t2, t3;
            ADD3(west(up, i), up[i], east(up, i), u0, u1);   /* three neighbours above */
            ADD3(west(dn, i), dn[i], east(dn, i), d0, d1);   /* three neighbours below */
            m0 = west(me, i) ^ east(me, i); m1 = west(me, i) & east(me, i);  /* left and right */
            ADD3(u0, d0, m0, t0, c1);        /* ones digit */
            ADD3(u1, d1, m1, p1, p2);        /* twos digit (partial) */
            t1 = p1 ^ c1; c2 = p1 & c1;
            t2 = p2 ^ c2; t3 = p2 & c2;      /* sum = t0 + 2t1 + 4t2 + 8t3 */
            /* live: sum==3 or (sum==2 and alive)  <=>  t1 & ~t2 & ~t3 & (t0 | alive) */
            next[y * W + i] = t1 & ~t2 & ~t3 & (t0 | me[i]);
        }
    }
}

int main(int argc, char **argv) {
    N = atoi(argv[1]); W = N / 64; GENS = atoi(argv[2]);
    u64 *a = calloc(N * W, 8), *b = calloc(N * W, 8);
    read_seed(argv[3], a);
    double t0 = now();
    for (int g = 0; g < GENS; g++) { step(a, b); u64 *t = a; a = b; b = t; }
    double t1 = now();
    long alive = 0;
    for (int i = 0; i < N * W; i++) alive += __builtin_popcountll(a[i]);
    printf("alive=%ld sim_ms=%.3f\n", alive, (t1 - t0) * 1e3);
    return 0;
}
