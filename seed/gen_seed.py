#!/usr/bin/env python3
"""Shared starting pattern: random.Random(42), density 0.3.
Each language's own RNG cannot reproduce the same sequence, so the pattern is
written to a file once and every implementation reads that same file.
File format: N lines, each N characters ('0' dead, '1' alive)."""
import random, sys
for n in (64, 128, 512):
    rng = random.Random(42)
    with open(f"start_{n}.txt", "w") as f:
        for _ in range(n):
            f.write("".join("1" if rng.random() < 0.3 else "0" for _ in range(n)) + "\n")
    print(n, "written")
