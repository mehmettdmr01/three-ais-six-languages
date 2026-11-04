import sys
import time


def main():
    n = int(sys.argv[1])
    gens = int(sys.argv[2])
    with open(sys.argv[3], "rb") as f:
        data = f.read()
    cells = bytes(c for c in data if c == 48 or c == 49)[: n * n]
    # Whole grid as one big integer: bit (r*n + c) is cell (r, c).
    tot = n * n
    g = int(cells.decode().ljust(tot, "0")[::-1], 2)
    full = (1 << tot) - 1
    # column masks
    row_last = 1 << (n - 1)
    last_col = 0
    for r in range(n):
        last_col |= row_last << (r * n)
    not_last = full ^ last_col
    first_col = full // ((1 << n) - 1) if n > 0 else 0  # bit 0 of each row
    not_first = full ^ first_col
    sh_up = n
    sh_dn = tot - n
    ne = n - 1

    t0 = time.perf_counter()
    for _ in range(gens):
        # neighbour grids: cell (r,c) reads from (r,c+1) for east, (r,c-1) for west
        e = ((g >> 1) & not_last) | ((g << ne) & last_col)
        w = ((g << 1) & not_first & full) | ((g >> ne) & first_col)
        # up neighbour of (r,c) is (r-1,c): bit shifted by +n, wrap
        def vert_up(x):
            return ((x << sh_up) | (x >> sh_dn)) & full

        def vert_dn(x):
            return (x >> sh_up) | ((x << sh_dn) & full)

        a = vert_up(w); b = vert_up(g); c = vert_up(e)
        t = a ^ b
        s1 = t ^ c
        c1 = (a & b) | (c & t)
        s2 = w ^ e
        c2 = w & e
        a = vert_dn(w); b = vert_dn(g); c = vert_dn(e)
        t = a ^ b
        s3 = t ^ c
        c3 = (a & b) | (c & t)
        t = s1 ^ s2
        on = t ^ s3
        k1 = (s1 & s2) | (s3 & t)
        u = c1 ^ c2
        v = c3 ^ k1
        par = u ^ v
        two = (c1 & c2) | (c3 & k1) | ((c1 | c2) & (c3 | k1))
        g = par & ~two & (on | g)
    ms = (time.perf_counter() - t0) * 1e3
    alive = g.bit_count() if hasattr(g, "bit_count") else bin(g).count("1")
    print("alive=%d sim_ms=%.3f" % (alive, ms))


main()
