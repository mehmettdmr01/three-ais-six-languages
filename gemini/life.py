import sys
import time
import numpy as np

def main():
    if len(sys.argv) < 4:
        sys.exit(1)

    N = int(sys.argv[1])
    GENS = int(sys.argv[2])
    filename = sys.argv[3]

    with open(filename, "rb") as f:
        file_bytes = f.read()

    W = (N + 63) // 64
    rem = N % 64
    last_mask = np.uint64(((1 << rem) - 1) if rem != 0 else 0xFFFFFFFFFFFFFFFF)
    last_bit_idx = np.uint64((rem - 1) if rem != 0 else 63)
    one = np.uint64(1)
    sixty_three = np.uint64(63)

    grid = np.zeros((N, W), dtype=np.uint64)

    file_pos = 0
    file_len = len(file_bytes)
    for r in range(N):
        if file_pos >= file_len:
            break
        c = 0
        while c < N and file_pos < file_len:
            b = file_bytes[file_pos]
            file_pos += 1
            if b == 49: # '1'
                grid[r, c // 64] |= np.uint64(1 << (c % 64))
                c += 1
            elif b == 48: # '0'
                c += 1
        while file_pos < file_len and (file_bytes[file_pos] == 13 or file_bytes[file_pos] == 10):
            file_pos += 1

    t0 = time.perf_counter()

    if GENS > 0:
        U = np.empty((N, W), dtype=np.uint64)
        D = np.empty((N, W), dtype=np.uint64)
        carry_L = np.empty((N, W), dtype=np.uint64)
        carry_R = np.empty((N, W), dtype=np.uint64)

        for _ in range(GENS):
            U[0] = grid[-1]
            U[1:] = grid[:-1]
            D[-1] = grid[0]
            D[:-1] = grid[1:]

            u_xor_m = U ^ grid
            S1 = u_xor_m ^ D
            C1 = (U & grid) | (D & u_xor_m)

            S1_L = S1 << one
            if W == 1:
                S1_L |= (S1 >> last_bit_idx)
            else:
                carry_L[:, 1:] = S1[:, :-1] >> sixty_three
                carry_L[:, 0] = (S1[:, -1] >> last_bit_idx) & one
                S1_L |= carry_L
            S1_L[:, -1] &= last_mask

            S1_R = S1 >> one
            if W == 1:
                S1_R |= ((S1 & one) << last_bit_idx)
            else:
                carry_R[:, :-1] = (S1[:, 1:] & one) << sixty_three
                carry_R[:, -1] = (S1[:, 0] & one) << last_bit_idx
                S1_R |= carry_R
            S1_R[:, -1] &= last_mask

            C1_L = C1 << one
            if W == 1:
                C1_L |= (C1 >> last_bit_idx)
            else:
                carry_L[:, 1:] = C1[:, :-1] >> sixty_three
                carry_L[:, 0] = (C1[:, -1] >> last_bit_idx) & one
                C1_L |= carry_L
            C1_L[:, -1] &= last_mask

            C1_R = C1 >> one
            if W == 1:
                C1_R |= ((C1 & one) << last_bit_idx)
            else:
                carry_R[:, :-1] = (C1[:, 1:] & one) << sixty_three
                carry_R[:, -1] = (C1[:, 0] & one) << last_bit_idx
                C1_R |= carry_R
            C1_R[:, -1] &= last_mask

            s_xor = S1_L ^ S1
            s_s = s_xor ^ S1_R
            c_s = (S1_L & S1) | (s_xor & S1_R)

            c_xor = C1_L ^ C1
            s_c = c_xor ^ C1_R
            c_c = (C1_L & C1) | (c_xor & C1_R)

            b0 = s_s
            b1 = s_c ^ c_s
            c_sc = s_c & c_s
            b2 = c_c ^ c_sc
            b3 = c_c & c_sc

            x = b0 & b1
            y = b0 | b1

            grid = (~b3) & ((x & ~b2) | (~y & b2 & grid))
            grid[:, -1] &= last_mask

    t1 = time.perf_counter()
    sim_ms = int(round((t1 - t0) * 1000.0))

    alive = int(np.sum(np.bitwise_count(grid)))
    print(f"alive={alive} sim_ms={sim_ms}")

if __name__ == "__main__":
    main()
