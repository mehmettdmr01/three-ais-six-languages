# Conway's Game of Life on an N x N torus, bit-parallel with NumPy: 64 cells per uint64.
# Each row is stored as [ghost | W words | ghost] and the row sums have ghost rows above and
# below, so every step is one flat, contiguous ufunc call into a preallocated buffer.
import sys
import time

import numpy as np


def main():
    if len(sys.argv) < 4:
        sys.exit(f"usage: {sys.argv[0]} N GENS SEED_FILE")
    n, gens, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with open(path, 'rb') as f:
        raw = np.frombuffer(f.read(), dtype=np.uint8)
    raw = raw[(raw == 48) | (raw == 49)][:n * n]
    cells = np.zeros(n * n, dtype=bool)
    cells[:raw.size] = raw == 49

    w = (n + 63) // 64
    w2 = w + 2
    m = n * w2
    lastbit = (n - 1) & 63
    partial = n & 63 != 0
    lastmask = np.uint64((1 << (n & 63)) - 1)
    bits = np.zeros((n, w * 64), dtype=bool)
    bits[:, :n] = cells.reshape(n, n)
    packed = np.packbits(bits, axis=1, bitorder='little').view('<u8').astype(np.uint64)

    g = np.zeros((n, w2), np.uint64)
    g[:, 1:w + 1] = packed
    ng = np.zeros_like(g)
    gf, ngf = g.ravel(), ng.ravel()

    u1, u63, ulb = np.uint64(1), np.uint64(63), np.uint64(lastbit)
    ughost = np.uint64(63 - lastbit)
    L, R, P, Q, S, T, m0, m1 = (np.zeros(m, np.uint64) for _ in range(8))
    R2 = R.reshape(n, w2)
    col = np.zeros(n, np.uint64)
    h0 = np.zeros((n + 2) * w2, np.uint64)
    h1 = np.zeros((n + 2) * w2, np.uint64)
    a0, b0, c0 = h0[:m], h0[w2:w2 + m], h0[2 * w2:]
    a1, b1, c1 = h1[:m], h1[w2:w2 + m], h1[2 * w2:]
    top, first, last, bottom = h0[:w2], h0[w2:2 * w2], h0[m:m + w2], h0[m + w2:]
    top1, first1, last1, bottom1 = h1[:w2], h1[w2:2 * w2], h1[m:m + w2], h1[m + w2:]

    band, bor, bxor = np.bitwise_and, np.bitwise_or, np.bitwise_xor
    lsh, rsh, copyto = np.left_shift, np.right_shift, np.copyto

    t0 = time.perf_counter()
    for _ in range(gens):
        # Ghost words: left one has cell N-1 at bit 63, right one has cell 0 at bit 0.
        lsh(g[:, w], ughost, g[:, 0])
        copyto(g[:, w + 1], g[:, 1])
        # L: bit i = cell i-1, R: bit i = cell i+1.
        lsh(gf[1:], u1, L[1:])
        rsh(gf[:-1], u63, P[1:])
        bor(L[1:], P[1:], L[1:])
        rsh(gf[:-1], u1, R[:-1])
        lsh(gf[1:], u63, P[:-1])
        bor(R[:-1], P[:-1], R[:-1])
        if partial:  # cell 0 is the right neighbour of cell N-1, at bit lastbit
            band(g[:, 1], u1, col)
            lsh(col, ulb, col)
            bor(R2[:, w], col, R2[:, w])
        # Row sums: m = left + right (2 bits), h = left + self + right (2 bits).
        bxor(L, R, m0)
        band(L, R, m1)
        bxor(m0, gf, b0)
        band(m0, gf, P)
        bor(m1, P, b1)
        copyto(top, last)
        copyto(bottom, first)
        copyto(top1, last1)
        copyto(bottom1, first1)
        # 8-neighbour count n = h(above) + m(row) + h(below); alive next iff (n | self) == 3,
        # i.e. the twos-level sum is exactly one and (ones | self).
        bxor(a0, m0, P)
        band(a0, m0, Q)
        bxor(P, c0, S)          # ones
        band(P, c0, P)
        bor(Q, P, Q)            # carry into twos
        bor(S, gf, S)           # ones | self
        bxor(a1, m1, P)         # s
        band(a1, m1, T)
        bxor(c1, Q, m0)         # t
        band(c1, Q, Q)
        bor(T, Q, T)            # some pair at twos level
        bxor(P, m0, P)          # s ^ t
        bor(P, T, Q)
        bxor(Q, T, Q)           # exactly one at twos level
        band(S, Q, ngf)
        if partial:
            ng[:, w] &= lastmask
        g, ng = ng, g
        gf, ngf = ngf, gf
    ms = (time.perf_counter() - t0) * 1e3

    live = np.ascontiguousarray(g[:, 1:w + 1])
    if hasattr(np, 'bitwise_count'):
        alive = int(np.bitwise_count(live).sum())
    else:
        alive = int(np.unpackbits(live.view(np.uint8)).sum())
    print(f"alive={alive} sim_ms={ms:.3f}")


main()
