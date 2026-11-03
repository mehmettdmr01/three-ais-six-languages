const fs = require("fs");

function popcount32(n) {
    n = n - ((n >>> 1) & 0x55555555);
    n = (n & 0x33333333) + ((n >>> 2) & 0x33333333);
    return (((n + (n >>> 4)) & 0x0F0F0F0F) * 0x01010101) >>> 24;
}

function main() {
    const args = process.argv.slice(2);
    if (args.length < 3) {
        process.exit(1);
    }

    const N = parseInt(args[0], 10);
    const GENS = parseInt(args[1], 10);
    const filename = args[2];

    const fileBuf = fs.readFileSync(filename);

    const W = Math.ceil(N / 32);
    const rem = N % 32;
    const last_mask = rem === 0 ? -1 : ((1 << rem) - 1);
    const last_bit_idx = rem === 0 ? 31 : (rem - 1);

    let cur = new Int32Array(N * W);
    let nxt = new Int32Array(N * W);

    let file_pos = 0;
    const file_len = fileBuf.length;

    for (let r = 0; r < N && file_pos < file_len; r++) {
        let c = 0;
        while (c < N && file_pos < file_len) {
            const b = fileBuf[file_pos++];
            if (b === 49) { // '1'
                cur[r * W + (c >> 5)] |= (1 << (c & 31));
                c++;
            } else if (b === 48) { // '0'
                c++;
            }
        }
        while (file_pos < file_len && (fileBuf[file_pos] === 13 || fileBuf[file_pos] === 10)) {
            file_pos++;
        }
    }

    const S1 = new Int32Array(W);
    const C1 = new Int32Array(W);
    const S1_L = new Int32Array(W);
    const S1_R = new Int32Array(W);
    const C1_L = new Int32Array(W);
    const C1_R = new Int32Array(W);

    const t0 = performance.now();

    for (let g = 0; g < GENS; g++) {
        for (let r = 0; r < N; r++) {
            const r_up = r === 0 ? N - 1 : r - 1;
            const r_dn = r === N - 1 ? 0 : r + 1;

            const off_u = r_up * W;
            const off_m = r * W;
            const off_d = r_dn * W;

            for (let k = 0; k < W; k++) {
                const u = cur[off_u + k];
                const m = cur[off_m + k];
                const d = cur[off_d + k];
                const u_xor_m = u ^ m;
                S1[k] = u_xor_m ^ d;
                C1[k] = (u & m) | (d & u_xor_m);
            }

            for (let k = 0; k < W; k++) {
                let L = S1[k] << 1;
                if (k > 0) L |= (S1[k - 1] >>> 31) & 1;
                else L |= (S1[W - 1] >>> last_bit_idx) & 1;
                if (k === W - 1) L &= last_mask;
                S1_L[k] = L;

                let R = S1[k] >>> 1;
                if (k < W - 1) R |= (S1[k + 1] & 1) << 31;
                else R |= (S1[0] & 1) << last_bit_idx;
                if (k === W - 1) R &= last_mask;
                S1_R[k] = R;

                L = C1[k] << 1;
                if (k > 0) L |= (C1[k - 1] >>> 31) & 1;
                else L |= (C1[W - 1] >>> last_bit_idx) & 1;
                if (k === W - 1) L &= last_mask;
                C1_L[k] = L;

                R = C1[k] >>> 1;
                if (k < W - 1) R |= (C1[k + 1] & 1) << 31;
                else R |= (C1[0] & 1) << last_bit_idx;
                if (k === W - 1) R &= last_mask;
                C1_R[k] = R;
            }

            for (let k = 0; k < W; k++) {
                const sL = S1_L[k], sC = S1[k], sR = S1_R[k];
                const cL = C1_L[k], cC = C1[k], cR = C1_R[k];

                const s_xor = sL ^ sC;
                const s_s = s_xor ^ sR;
                const c_s = (sL & sC) | (s_xor & sR);

                const c_xor = cL ^ cC;
                const s_c = c_xor ^ cR;
                const c_c = (cL & cC) | (c_xor & cR);

                const b0 = s_s;
                const b1 = s_c ^ c_s;
                const c_sc = s_c & c_s;
                const b2 = c_c ^ c_sc;
                const b3 = c_c & c_sc;

                const x = b0 & b1;
                const y = b0 | b1;
                const m = cur[off_m + k];

                let res = (~b3) & ((x & ~b2) | (~y & b2 & m));
                if (k === W - 1) res &= last_mask;
                nxt[off_m + k] = res;
            }
        }
        const tmp = cur;
        cur = nxt;
        nxt = tmp;
    }

    const t1 = performance.now();
    const sim_ms = Math.round(t1 - t0);

    let alive = 0;
    for (let i = 0; i < N * W; i++) {
        alive += popcount32(cur[i]);
    }

    console.log(`alive=${alive} sim_ms=${sim_ms}`);
}

main();
