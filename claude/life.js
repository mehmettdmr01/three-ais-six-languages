'use strict';
// Conway's Game of Life on an N x N torus, bit-parallel: 32 cells per Int32Array word.
const fs = require('fs');

// One generation. For each row: 3-cell horizontal sums (left + self + right) as two
// bit planes h0/h1, and 2-cell sums (left + right) as m0/m1. Then for each row the
// 8-neighbour count n = above3 + mid2 + below3, and alive next iff (n | self) == 3.
function step(g, ng, h0, h1, m0, m1, N, W, lastbit, lastmask) {
  for (let y = 0; y < N; y++) {
    const o = y * W;
    if (W === 1) {
      const c = g[o];
      const l = (c << 1) | ((c >>> lastbit) & 1);
      const r = (c >>> 1) | ((c & 1) << lastbit);
      const x = l ^ r, a = l & r;
      h0[o] = x ^ c;
      h1[o] = a | (x & c);
      m0[o] = x;
      m1[o] = a;
      continue;
    }
    let prev = g[o + W - 1] >>> lastbit << 31;
    let c = g[o];
    for (let w = 0; w < W - 1; w++) {
      const next = g[o + w + 1];
      const l = (c << 1) | (prev >>> 31);
      const r = (c >>> 1) | (next << 31);
      const x = l ^ r, a = l & r;
      h0[o + w] = x ^ c;
      h1[o + w] = a | (x & c);
      m0[o + w] = x;
      m1[o + w] = a;
      prev = c;
      c = next;
    }
    {
      const w = W - 1;
      const l = (c << 1) | (prev >>> 31);
      const r = (c >>> 1) | ((g[o] & 1) << lastbit);
      const x = l ^ r, a = l & r;
      h0[o + w] = x ^ c;
      h1[o + w] = a | (x & c);
      m0[o + w] = x;
      m1[o + w] = a;
    }
  }
  for (let y = 0; y < N; y++) {
    const mid = y * W;
    const up = (y === 0 ? N - 1 : y - 1) * W;
    const dn = (y === N - 1 ? 0 : y + 1) * W;
    for (let w = 0; w < W; w++) {
      const a0 = h0[up + w], b0 = m0[mid + w], c0 = h0[dn + w];
      const p = a0 ^ b0;
      const ones = p ^ c0;
      const carry = (a0 & b0) | (p & c0);
      const a1 = h1[up + w], b1 = m1[mid + w], c1 = h1[dn + w];
      const s = a1 ^ b1, t = c1 ^ carry;
      const exactlyOne = (s ^ t) & ~((a1 & b1) | (c1 & carry));
      ng[mid + w] = (ones | g[mid + w]) & exactlyOne;
    }
    ng[mid + W - 1] &= lastmask;
  }
}

function popcount32(v) {
  v = v - ((v >>> 1) & 0x55555555);
  v = (v & 0x33333333) + ((v >>> 2) & 0x33333333);
  return (((v + (v >>> 4)) & 0x0f0f0f0f) * 0x01010101) >>> 24;
}

function main() {
  const args = process.argv.slice(2);
  if (args.length < 3) {
    process.stderr.write('usage: node life.js N GENS SEED_FILE\n');
    process.exit(1);
  }
  const N = parseInt(args[0], 10);
  const GENS = parseInt(args[1], 10);
  const data = fs.readFileSync(args[2]);

  const W = (N + 31) >>> 5;
  const lastbit = (N - 1) & 31;
  const lastmask = (N & 31) ? ((1 << (N & 31)) - 1) : -1;
  const cells = N * W;
  let g = new Int32Array(cells);
  let ng = new Int32Array(cells);
  const h0 = new Int32Array(cells), h1 = new Int32Array(cells);
  const m0 = new Int32Array(cells), m1 = new Int32Array(cells);

  const total = N * N;
  let k = 0;
  for (let i = 0; i < data.length && k < total; i++) {
    const ch = data[i];
    if (ch === 48 || ch === 49) {
      if (ch === 49) {
        const y = Math.floor(k / N), x = k - y * N;
        g[y * W + (x >>> 5)] |= 1 << (x & 31);
      }
      k++;
    }
  }

  const t0 = process.hrtime.bigint();
  for (let gen = 0; gen < GENS; gen++) {
    step(g, ng, h0, h1, m0, m1, N, W, lastbit, lastmask);
    const tmp = g; g = ng; ng = tmp;
  }
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;

  let alive = 0;
  for (let i = 0; i < cells; i++) alive += popcount32(g[i]);
  process.stdout.write(`alive=${alive} sim_ms=${ms.toFixed(3)}\n`);
}

main();
