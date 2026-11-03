"""NumPy with four rolls instead of eight: sum three columns, then three rows, subtract the cell.
A faster loader too. Same rule: (count | cell) == 3."""
import sys, time, numpy as np

def load(path, n):
    raw = np.fromfile(path, dtype=np.uint8)
    return (raw[raw != 10].reshape(n, n) == ord("1")).astype(np.uint8)

def step(g):
    h = g + np.roll(g, 1, 1) + np.roll(g, -1, 1)
    c = h + np.roll(h, 1, 0) + np.roll(h, -1, 0) - g
    return ((c | g) == 3).astype(np.uint8)

if __name__ == "__main__":
    n, gens, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    g = load(path, n)
    t0 = time.perf_counter()
    for _ in range(gens):
        g = step(g)
    sim = (time.perf_counter() - t0) * 1e3
    print(f"alive={int(g.sum())} sim_ms={sim:.3f}")
