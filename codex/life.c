#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

static void halo(unsigned char *a, size_t n, size_t stride) {
    for (size_t i = 1; i <= n; ++i) {
        size_t r = i * stride;
        a[r] = a[r + n];
        a[r + n + 1] = a[r + 1];
    }
    for (size_t j = 0; j < stride; ++j) {
        a[j] = a[n * stride + j];
        a[(n + 1) * stride + j] = a[stride + j];
    }
}

static unsigned long step(const unsigned char * restrict a,
                          unsigned char * restrict b, size_t n, size_t stride) {
    unsigned long alive = 0;
    for (size_t i = 1; i <= n; ++i) {
        size_t k = i * stride + 1;
        for (size_t j = 1; j <= n; ++j, ++k) {
            unsigned char s = a[k-stride-1] + a[k-stride] + a[k-stride+1]
                            + a[k-1] + a[k+1]
                            + a[k+stride-1] + a[k+stride] + a[k+stride+1];
            unsigned char v = (s == 3) | ((s == 2) & a[k]);
            b[k] = v;
            alive += v;
        }
    }
    return alive;
}

int main(int argc, char **argv) {
    if (argc != 4) return 1;
    size_t n = strtoull(argv[1], NULL, 10), gens = strtoull(argv[2], NULL, 10);
    if (!n || n > (size_t)-1 / (n + 2) - 2) return 1;
    size_t stride = n + 2, bytes = stride * stride;
    unsigned char *a = calloc(bytes, 1), *b = calloc(bytes, 1);
    FILE *f = fopen(argv[3], "rb");
    if (!a || !b || !f) return 1;
    for (size_t i = 1; i <= n; ++i)
        for (size_t j = 1; j <= n; ++j) {
            int c; do { c = fgetc(f); } while (c == '\n' || c == '\r');
            if (c == EOF) return 1;
            a[i * stride + j] = (c == '1');
        }
    fclose(f);
    struct timeval t0, t1; gettimeofday(&t0, NULL);
    unsigned long alive = 0;
    if (!gens) for (size_t i = 1; i <= n; ++i) for (size_t j = 1; j <= n; ++j) alive += a[i*stride+j];
    for (size_t g = 0; g < gens; ++g) {
        halo(a, n, stride);
        alive = step(a, b, n, stride);
        unsigned char *x = a; a = b; b = x;
    }
    gettimeofday(&t1, NULL);
    double ms = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_usec-t0.tv_usec)/1000.0;
    printf("alive=%lu sim_ms=%.3f\n", alive, ms);
    free(a); free(b);
    return 0;
}
