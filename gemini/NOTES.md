# Conway's Game of Life: Performance Optimizations

Across all six implementations, the core algorithm is a bit-parallel simulation using a 9-cell full-adder network: cells are packed into words (64-bit words for C, Rust, Go, Zig, and Python NumPy; 32-bit words for JavaScript), and the state update for all bits in a word is computed in parallel with approximately 20 bitwise operations, while torus wrapping is handled via word-level barrel and carry shifts.

### C (`life.c`)
Packed 64 cells per `uint64_t` using a 9-cell full-adder bitwise formulation with `__restrict__` pointers and pointer-swapping between generations to enable full compiler auto-vectorization and zero-copy iteration, paired with single-pass whole-file buffering and `__builtin_popcountll`.

### Rust (`life.rs`)
Used contiguous `Vec<u64>` buffers with bit-parallel full-adder arithmetic and `std::mem::swap` to eliminate per-generation allocations, relying on `u64::count_ones` for hardware popcount and bulk file ingestion.

### Go (`life.go`)
Implemented flat 64-bit bitboard slices with branchless inner adder evaluations and slice header swapping, leveraging `math/bits.OnesCount64` for hardware popcount instructions on ARM64 and `os.ReadFile` for minimal I/O overhead.

### Zig (`life.zig`)
Leveraged `-O ReleaseFast` and `@popCount` hardware intrinsics over contiguous 64-bit slices, utilizing the 9-cell bit-parallel network to allow LLVM to unroll and auto-vectorize bitwise operations with zero runtime safety checks.

### Python (`life.py`)
Vectorized the 64-bit bit-parallel adder network across all rows simultaneously using 2D NumPy `uint64` arrays and in-place/preallocated ufunc operations, completely bypassing Python interpreter loop overhead during simulation.

### JavaScript (`life.js`)
Employed 32-bit words inside flat `Int32Array` typed arrays to ensure V8 keeps all bitwise arithmetic in 32-bit CPU registers as unboxed SMIs (preventing BigInt heap allocations), combined with reusable scratch buffers and a parallel SWAR bitwise popcount.
