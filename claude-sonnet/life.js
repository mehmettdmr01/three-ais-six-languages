"use strict";
const fs = require("fs");
const N = parseInt(process.argv[2], 10);
const G = parseInt(process.argv[3], 10);
const buf = fs.readFileSync(process.argv[4]);
const W = Math.ceil(N / 32);
const L = N - 32 * (W - 1);
const lm = L === 32 ? -1 : ((1 << L) - 1) | 0;
let cur = new Int32Array(N * W);
let nxt = new Int32Array(N * W);
const we = new Int32Array(N * W);
const ee = new Int32Array(N * W);
{
  let k = 0;
  const tot = N * N;
  for (let i = 0; i < buf.length && k < tot; i++) {
    const c = buf[i];
    if (c === 49) {
      const r = (k / N) | 0, q = k - r * N;
      cur[r * W + (q >> 5)] |= 1 << (q & 31);
      k++;
    } else if (c === 48) k++;
  }
}
const t0 = process.hrtime.bigint();
for (let g = 0; g < G; g++) {
  for (let r = 0; r < N; r++) {
    const base = r * W;
    for (let i = 0; i < W; i++) {
      const x = cur[base + i];
      let e, w;
      if (i < W - 1) e = (x >>> 1) | (cur[base + i + 1] << 31);
      else e = (x >>> 1) | ((cur[base] & 1) << (L - 1));
      if (i > 0) w = (x << 1) | (cur[base + i - 1] >>> 31);
      else w = (x << 1) | ((cur[base + W - 1] >>> (L - 1)) & 1);
      if (i === W - 1) w &= lm;
      we[base + i] = w;
      ee[base + i] = e;
    }
  }
  for (let r = 0; r < N; r++) {
    const ru = (r === 0 ? N - 1 : r - 1) * W;
    const rd = (r === N - 1 ? 0 : r + 1) * W;
    const rm = r * W;
    for (let i = 0; i < W; i++) {
      let a = we[ru + i], b = cur[ru + i], c = ee[ru + i];
      const s1 = a ^ b ^ c, c1 = (a & b) | (c & (a ^ b));
      const d = we[rm + i], e = ee[rm + i];
      const s2 = d ^ e, c2 = d & e;
      a = we[rd + i]; b = cur[rd + i]; c = ee[rd + i];
      const s3 = a ^ b ^ c, c3 = (a & b) | (c & (a ^ b));
      const on = s1 ^ s2 ^ s3;
      const k1 = (s1 & s2) | (s3 & (s1 ^ s2));
      const par = c1 ^ c2 ^ c3 ^ k1;
      const two = (c1 & c2) | (c3 & k1) | ((c1 | c2) & (c3 | k1));
      nxt[rm + i] = par & ~two & (on | cur[rm + i]);
    }
  }
  const t = cur; cur = nxt; nxt = t;
}
const ms = Number(process.hrtime.bigint() - t0) / 1e6;
let alive = 0;
for (let i = 0; i < cur.length; i++) {
  let x = cur[i];
  x = x - ((x >>> 1) & 0x55555555);
  x = (x & 0x33333333) + ((x >>> 2) & 0x33333333);
  x = (x + (x >>> 4)) & 0x0f0f0f0f;
  alive += Math.imul(x, 0x01010101) >>> 24;
}
console.log(`alive=${alive} sim_ms=${ms.toFixed(3)}`);
