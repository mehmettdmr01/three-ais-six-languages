"""Array programming: NumPy, 8 neighbours via np.roll; no per-cell loop.
np.roll wraps around by itself, so the edges are toroidal."""
import sys, time, numpy as np

def load(path):
    return np.array([[c == "1" for c in line.rstrip("\n")] for line in open(path)], dtype=np.uint8)

def step(g):
    n = sum(np.roll(np.roll(g, dy, 0), dx, 1)
            for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    return ((n == 3) | ((n == 2) & (g == 1))).astype(np.uint8)

if __name__ == "__main__":
    n, gens, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    g = load(path)
    t0 = time.perf_counter()
    for _ in range(gens):
        g = step(g)
    sim = (time.perf_counter() - t0) * 1e3
    print(f"alive={int(g.sum())} sim_ms={sim:.3f}")
