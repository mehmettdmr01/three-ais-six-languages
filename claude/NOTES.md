# Notes

All six versions use the same algorithm. The grid is bit-packed, one bit per cell, so a
single word holds 64 cells (32 in JS). One generation is two passes of bitwise logic, with
no per-cell loops or branches:

1. For every row, shift the words left and right by one bit (carrying bits across word
   boundaries and wrapping the row ends), then store the sum left + self + right as two
   bit planes.
2. For every row, add the planes of the rows above, at and below with a small adder
   network and apply the rule to all 64 cells at once.

The row above row 0 is row N-1, and the row below row N-1 is row 0. The unused bits at the
end of each row are masked off. The file is read and packed before the timer starts, and
the live cells are counted with popcount after it stops.

Timings for `512 200 start_512.txt` on this M1. The machine was noisy, so each figure is a
range across runs: C ~1.4–2.4 ms, Rust ~1.5–2.3 ms, Zig ~1.3–1.7 ms, Go ~3–4 ms,
Python ~9.3 ms, JS ~13 ms.

- **C**: The bit-parallel algorithm, with `restrict` pointers and plain straight-line
  inner loops, so `clang -O2` vectorises them into 128-bit NEON operations (2 words, or
  128 cells, per instruction). The edge words are handled outside the loops, so the loop
  bodies have no branches.
- **Rust**: The same structure as C. Every row is re-sliced to its exact length before
  the inner loop, so LLVM drops the bounds checks and vectorises the loops at
  `opt-level=3`.
- **Go**: The same algorithm. Re-slicing to a known length removes most bounds checks,
  and the shift loop carries `prev`/`next` in registers. Go has no auto-vectoriser, so
  this one runs one 64-bit word at a time and is about 2x slower than C.
- **Zig**: The same algorithm, written with explicit `@Vector(2, u64)` SIMD for the inner
  loops, so it does not depend on the auto-vectoriser. `ReleaseFast` removes safety
  checks. It uses the new 0.17 `std.process.Init` / `std.Io` APIs.
- **Python**: NumPy operations on the whole bit-packed grid at once, about 30 calls per
  generation. Each call writes into a preallocated buffer, so nothing is allocated in the
  loop. Every row has a ghost word at each end, and the row sums have a ghost row above
  and below, so each call is one flat contiguous view. It also uses a cheaper
  8-neighbour test: alive next iff `(count | self) == 3`. Together these took it from
  ~18 ms to ~9 ms.
- **JavaScript**: Bit-parallel on `Int32Array` with 32-bit words, because that is what
  V8 compiles to native integer ops; BigInt is slow. The hot loop sits in one
  monomorphic function and uses the `(count | self) == 3` rule. About 4 ms of the total is
  V8 warm-up before the optimising compiler takes over, and I did not hide that.

Testing: `.tmp/harness.py` compares every program with a plain `np.roll` reference. It
covers sizes 1, 2, 3, 5, 31–33, 63–65, 100, 127–129, 200, 257, 512 and 513, plus
0 and 1 generations. All six programs pass, and they also agree on a 1000×1000 grid.
