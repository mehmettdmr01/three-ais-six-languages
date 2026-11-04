# Notes

All six programs use the same idea: the grid is bit-packed (one bit per cell) and each generation is computed with bit-parallel adders, so 64 cells (32 in JS) are updated per instruction. Wrap-around is handled for any N, not only multiples of 64: the left/right neighbour rows are shifted across word boundaries with a wrap at bit N-1, and the top/bottom rows wrap by row index. I checked N = 1, 2, 3, 31, 64, 65, 130 and 512 against a slow reference.

- **C**: 64-bit words, the 8 neighbours are summed with full/half adders built from XOR/AND/OR, and the rule is applied as "exactly one carry-2 bit set and (ones bit or alive)". Shifted west/east rows are precomputed once per generation and the buffers are swapped, with no allocation in the loop.
- **Rust**: same algorithm, using row slices so the bounds checks are hoisted out of the inner loop, with `u64::count_ones` for the final count.
- **Go**: same algorithm, with each row sliced up front so the compiler can drop most bounds checks; the AND-NOT operator (`&^`) is used for the rule.
- **Zig**: same algorithm in ReleaseFast with slices per row. Output uses `writerStreaming` so it works when stdout is a file as well as a pipe.
- **Python**: the whole N x N grid is one big Python integer (bit r*N+c), so one generation is about 40 big-int shift/AND/XOR operations over the entire grid. Row wrap and column wrap are done with masks and rotations, which avoids any per-cell Python loop.
- **JavaScript**: `Int32Array` with 32-bit words and the same adder logic, using only int32 operations (`>>>`, `|`, `^`) so V8 keeps everything in machine integers; the buffers are preallocated and swapped.
