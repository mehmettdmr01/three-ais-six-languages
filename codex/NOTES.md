# Implementation notes

- C: Uses two flat byte buffers with a one-cell copied halo, so the vector-friendly inner loop has only contiguous, wrap-free loads; the final generation's population is counted in that loop.
- Rust: Uses the same padded byte layout and raw pointers only inside the proven in-bounds update loop, avoiding bounds checks in the hot path.
- Go: Uses flat `[]byte` double buffers and `copy` for complete halo rows, keeping the generation loop allocation-free.
- Zig: Uses padded byte buffers and explicit 16-lane byte vectors in the update kernel, with a scalar tail for arbitrary widths.
- Python: Uses NumPy ufuncs on preallocated arrays; a reusable halo avoids `roll` temporaries and all generation work stays in native vectorized code. A correct byte-buffer fallback is included for installations without NumPy.
- JavaScript: Uses `Uint8Array` double buffers, a copied halo, and monomorphic numeric loops to give V8 a simple hot path.
