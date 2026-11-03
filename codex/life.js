'use strict';
const fs = require('fs');
const { performance } = require('perf_hooks');
const n = Number(process.argv[2]), gens = Number(process.argv[3]);
if (!(n > 0) || !Number.isInteger(gens)) process.exit(1);
const s = n + 2, size = s * s;
let a = new Uint8Array(size), b = new Uint8Array(size);
const rule = new Uint8Array(18); rule[5] = rule[6] = rule[7] = 1;
const data = fs.readFileSync(process.argv[4]); let q = 0;
for (let i=1; i<=n; ++i) for (let j=1; j<=n; ++j) {
  while (data[q] === 10 || data[q] === 13) ++q;
  a[i*s+j] = data[q++] === 49 ? 1 : 0;
}
function halo(x) {
  for (let i=1; i<=n; ++i) { const r=i*s; x[r]=x[r+n]; x[r+n+1]=x[r+1]; }
  x.set(x.subarray(n*s, n*s+s), 0); x.set(x.subarray(s, 2*s), (n+1)*s);
}
function step(x, y) {
  let live=0;
  for (let i=1; i<=n; ++i) for (let j=1,k=i*s+1; j<=n; ++j,++k) {
    const z=x[k-s-1]+x[k-s]+x[k-s+1]+x[k-1]+x[k+1]+x[k+s-1]+x[k+s]+x[k+s+1];
    const v=rule[(z<<1)|x[k]]; y[k]=v; live+=v;
  }
  return live;
}
const t0=performance.now(); let alive=0;
if (gens===0) for(let i=1;i<=n;++i) for(let j=1;j<=n;++j) alive+=a[i*s+j];
for(let g=0;g<gens;++g) { halo(a); alive=step(a,b); const t=a;a=b;b=t; }
console.log(`alive=${alive} sim_ms=${(performance.now()-t0).toFixed(3)}`);
