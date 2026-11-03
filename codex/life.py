import sys
import time
try:
    import numpy as np
except ModuleNotFoundError:
    np = None

n = int(sys.argv[1]); gens = int(sys.argv[2])
raw = open(sys.argv[3], "rb").read()
bits = raw.replace(b"\n", b"").replace(b"\r", b"")[:n*n]

if np is None:                         # Keeps the required program usable without NumPy.
    s = n + 2; a = bytearray(s*s); b = bytearray(s*s)
    for i in range(n): a[(i+1)*s+1:(i+1)*s+n+1] = bytes(x - 48 for x in bits[i*n:(i+1)*n])
    t0 = time.perf_counter()
    for _ in range(gens):
        for i in range(1, n+1):
            r = i*s; a[r] = a[r+n]; a[r+n+1] = a[r+1]
        a[:s] = a[n*s:(n+1)*s]; a[(n+1)*s:] = a[s:2*s]
        for i in range(1, n+1):
            k = i*s+1
            for _ in range(n):
                z = a[k-s-1]+a[k-s]+a[k-s+1]+a[k-1]+a[k+1]+a[k+s-1]+a[k+s]+a[k+s+1]
                b[k] = (z == 3) or (z == 2 and a[k]); k += 1
        a, b = b, a
    elapsed = (time.perf_counter()-t0)*1000
    alive = sum(a[i*s+1:i*s+n+1].count(1) for i in range(1, n+1))
else:
    a = np.frombuffer(bits, dtype=np.uint8).copy(); a -= ord("0"); a = a.reshape(n, n)
    b = np.empty_like(a); count = np.empty_like(a); mask = np.empty_like(a, dtype=bool)
    p = np.empty((n + 2, n + 2), dtype=np.uint8)
    t0 = time.perf_counter()
    for _ in range(gens):
        # A one-cell halo makes every neighbour slice contiguous and avoids roll's allocations.
        p[1:-1, 1:-1] = a
        p[0, 1:-1] = a[-1]; p[-1, 1:-1] = a[0]
        p[1:-1, 0] = a[:, -1]; p[1:-1, -1] = a[:, 0]
        p[0, 0] = a[-1, -1]; p[0, -1] = a[-1, 0]; p[-1, 0] = a[0, -1]; p[-1, -1] = a[0, 0]
        np.add(p[:-2,:-2], p[:-2,1:-1], out=count)
        count += p[:-2,2:]; count += p[1:-1,:-2]; count += p[1:-1,2:]
        count += p[2:,:-2]; count += p[2:,1:-1]; count += p[2:,2:]
        np.equal(count, 3, out=b)
        np.equal(count, 2, out=mask); np.logical_and(mask, a, out=mask); np.logical_or(b, mask, out=b)
        a, b = b, a
    elapsed = (time.perf_counter()-t0)*1000
    alive = int(a.sum())
print(f"alive={alive} sim_ms={elapsed:.3f}")
