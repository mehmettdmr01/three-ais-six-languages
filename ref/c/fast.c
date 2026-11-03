/* Same as fast_int.c, but the neighbour count is one byte (it never exceeds 8), so the vector loop
   stays in 16 byte-wide lanes. */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static int N, GENS;
static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static void read_seed(const char *path, unsigned char *g) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); exit(1); }
    size_t len = (size_t)(N + 1) * N;
    char *t = malloc(len);
    len = fread(t, 1, len, f);
    fclose(f);
    for (size_t i = 0, j = 0; i < len; i++) if (t[i] != '\n') g[j++] = t[i] == '1';
    free(t);
}
static inline unsigned char rule(unsigned char n, unsigned char c) { return (n == 3) | ((n == 2) & c); }
static void step(const unsigned char *cur, unsigned char *next) {
    for (int y = 0; y < N; y++) {
        const unsigned char *u = cur + (y == 0 ? N - 1 : y - 1) * N, *m = cur + y * N, *d = cur + (y == N - 1 ? 0 : y + 1) * N;
        unsigned char *o = next + y * N;
        for (int x = 1; x < N - 1; x++) {
            unsigned char n = u[x-1] + u[x] + u[x+1] + m[x-1] + m[x+1] + d[x-1] + d[x] + d[x+1];
            o[x] = rule(n, m[x]);
        }
        int l = N - 1, r = 1;
        o[0] = rule(u[l] + u[0] + u[r] + m[l] + m[r] + d[l] + d[0] + d[r], m[0]);
        l = N - 2; r = 0;
        o[N-1] = rule(u[l] + u[N-1] + u[r] + m[l] + m[r] + d[l] + d[N-1] + d[r], m[N-1]);
    }
}
int main(int argc, char **argv) {
    N = atoi(argv[1]); GENS = atoi(argv[2]);
    unsigned char *a = malloc(N * N), *b = malloc(N * N);
    read_seed(argv[3], a);
    double t0 = now();
    for (int g = 0; g < GENS; g++) { step(a, b); unsigned char *t = a; a = b; b = t; }
    double t1 = now();
    long alive = 0; for (int i = 0; i < N * N; i++) alive += a[i];
    printf("alive=%ld sim_ms=%.3f\n", alive, (t1 - t0) * 1e3); return 0;
}
