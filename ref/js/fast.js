// Reference JavaScript, written the same way as c/fast.c in the V5 repo: one byte per cell,
// first and last column handled separately so the inner loop has no wrap-around arithmetic.
const fs = require("fs");
const N = +process.argv[2], GENS = +process.argv[3];
const text = fs.readFileSync(process.argv[4]);
let a = new Uint8Array(N * N), b = new Uint8Array(N * N);
for (let i = 0, j = 0; i < text.length && j < N * N; i++) if (text[i] !== 10) a[j++] = text[i] === 49 ? 1 : 0;
const rule = (n, c) => (n === 3 || (n === 2 && c === 1)) ? 1 : 0;
function step(cur, next) {
  for (let y = 0; y < N; y++) {
    const u = (y === 0 ? N - 1 : y - 1) * N, m = y * N, d = (y === N - 1 ? 0 : y + 1) * N;
    for (let x = 1; x < N - 1; x++) {
      const n = cur[u + x - 1] + cur[u + x] + cur[u + x + 1] + cur[m + x - 1] + cur[m + x + 1] + cur[d + x - 1] + cur[d + x] + cur[d + x + 1];
      next[m + x] = rule(n, cur[m + x]);
    }
    for (const x of [0, N - 1]) {
      const l = x === 0 ? N - 1 : x - 1, r = x === N - 1 ? 0 : x + 1;
      const n = cur[u + l] + cur[u + x] + cur[u + r] + cur[m + l] + cur[m + r] + cur[d + l] + cur[d + x] + cur[d + r];
      next[m + x] = rule(n, cur[m + x]);
    }
  }
}
const t0 = process.hrtime.bigint();
for (let g = 0; g < GENS; g++) { step(a, b); const t = a; a = b; b = t; }
const t1 = process.hrtime.bigint();
let alive = 0; for (let i = 0; i < N * N; i++) alive += a[i];
console.log(`alive=${alive} sim_ms=${(Number(t1 - t0) / 1e6).toFixed(3)}`);
