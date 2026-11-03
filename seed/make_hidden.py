#!/usr/bin/env python3
"""The hidden test seeds the agents never saw: same format and density as start_512.txt, other sizes and RNG seeds."""
import random
for n, s in ((300, 7), (1000, 11), (64, 3)):
    rng = random.Random(s)
    with open(f"hidden_{n}.txt", "w") as f:
        for _ in range(n):
            f.write("".join("1" if rng.random() < 0.3 else "0" for _ in range(n)) + "\n")
