// Conway's Game of Life on an N x N torus, bit-parallel: 64 cells per u64.
const std = @import("std");

const V = @Vector(2, u64);

// Horizontal 3-cell sum (left + self + right) of one row, as two bit planes.
inline fn put(l: u64, c: u64, r: u64, h0: *u64, h1: *u64) void {
    const x = l ^ c;
    h0.* = x ^ r;
    h1.* = (l & c) | (x & r);
}

fn hsumRow(r: []const u64, h0: []u64, h1: []u64, lastbit: u6) void {
    const w = r.len;
    if (w == 1) {
        const c = r[0];
        put((c << 1) | ((c >> lastbit) & 1), c, (c >> 1) | ((c & 1) << lastbit), &h0[0], &h1[0]);
        return;
    }
    {
        const c = r[0];
        put((c << 1) | ((r[w - 1] >> lastbit) & 1), c, (c >> 1) | (r[1] << 63), &h0[0], &h1[0]);
    }
    var i: usize = 1;
    while (i + 2 < w) : (i += 2) {
        const c: V = r[i..][0..2].*;
        const p: V = r[i - 1 ..][0..2].*;
        const n: V = r[i + 1 ..][0..2].*;
        const l = (c << @splat(1)) | (p >> @splat(63));
        const rr = (c >> @splat(1)) | (n << @splat(63));
        const x = l ^ c;
        h0[i..][0..2].* = x ^ rr;
        h1[i..][0..2].* = (l & c) | (x & rr);
    }
    while (i < w - 1) : (i += 1) {
        const c = r[i];
        put((c << 1) | (r[i - 1] >> 63), c, (c >> 1) | (r[i + 1] << 63), &h0[i], &h1[i]);
    }
    {
        const c = r[w - 1];
        put((c << 1) | (r[w - 2] >> 63), c, (c >> 1) | ((r[0] & 1) << lastbit), &h0[w - 1], &h1[w - 1]);
    }
}

// Next state from the 3-cell sums of the rows above (a), at (b) and below (c).
// Total of the 3x3 block (self included): alive next iff total == 3, or total == 4 and alive.
inline fn rule(comptime T: type, a0: T, a1: T, b0: T, b1: T, c0: T, c1: T, cur: T) T {
    const p = a0 ^ b0;
    const ones = p ^ c0;
    const carry = (a0 & b0) | (p & c0);
    const s = a1 ^ b1;
    const sc = a1 & b1;
    const t = c1 ^ carry;
    const tc = c1 & carry;
    const x = s ^ t;
    const eq3 = ones & x & ~(sc | tc);
    const eq4 = ~(ones | x) & ((s & t) | (sc ^ tc));
    return eq3 | (cur & eq4);
}

fn stepRow(a0: []const u64, a1: []const u64, b0: []const u64, b1: []const u64, c0: []const u64, c1: []const u64, cur: []const u64, out: []u64) void {
    const w = out.len;
    var i: usize = 0;
    while (i + 2 <= w) : (i += 2) {
        out[i..][0..2].* = rule(V, a0[i..][0..2].*, a1[i..][0..2].*, b0[i..][0..2].*, b1[i..][0..2].*, c0[i..][0..2].*, c1[i..][0..2].*, cur[i..][0..2].*);
    }
    if (i < w) out[i] = rule(u64, a0[i], a1[i], b0[i], b1[i], c0[i], c1[i], cur[i]);
}

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    const alloc = init.arena.allocator();
    const args = try init.minimal.args.toSlice(alloc);
    if (args.len < 4) {
        std.debug.print("usage: {s} N GENS SEED_FILE\n", .{args[0]});
        std.process.exit(1);
    }
    const n = try std.fmt.parseInt(usize, args[1], 10);
    const gens = try std.fmt.parseInt(u64, args[2], 10);
    const data = try std.Io.Dir.cwd().readFileAlloc(io, args[3], alloc, .unlimited);

    const w = (n + 63) / 64;
    const lastbit: u6 = @intCast((n - 1) & 63);
    const lastmask: u64 = if (n & 63 != 0) (@as(u64, 1) << @intCast(n & 63)) - 1 else ~@as(u64, 0);
    const cells = n * w;
    var g = try alloc.alloc(u64, cells);
    var ng = try alloc.alloc(u64, cells);
    const h0 = try alloc.alloc(u64, cells);
    const h1 = try alloc.alloc(u64, cells);
    @memset(g, 0);
    @memset(ng, 0);

    const total = n * n;
    var k: usize = 0;
    for (data) |ch| {
        if (k >= total) break;
        if (ch == '0' or ch == '1') {
            if (ch == '1') {
                const y = k / n;
                const x = k % n;
                g[y * w + x / 64] |= @as(u64, 1) << @intCast(x & 63);
            }
            k += 1;
        }
    }

    const t0 = std.Io.Timestamp.now(io, .awake);
    var gen: u64 = 0;
    while (gen < gens) : (gen += 1) {
        var y: usize = 0;
        while (y < n) : (y += 1) {
            const o = y * w;
            hsumRow(g[o .. o + w], h0[o .. o + w], h1[o .. o + w], lastbit);
        }
        y = 0;
        while (y < n) : (y += 1) {
            const up = (if (y == 0) n - 1 else y - 1) * w;
            const mid = y * w;
            const dn = (if (y == n - 1) 0 else y + 1) * w;
            const out = ng[mid .. mid + w];
            stepRow(h0[up .. up + w], h1[up .. up + w], h0[mid .. mid + w], h1[mid .. mid + w], h0[dn .. dn + w], h1[dn .. dn + w], g[mid .. mid + w], out);
            out[w - 1] &= lastmask;
        }
        const tmp = g;
        g = ng;
        ng = tmp;
    }
    const ns = t0.untilNow(io, .awake).toNanoseconds();
    const ms = @as(f64, @floatFromInt(ns)) / 1e6;

    var alive: u64 = 0;
    for (g) |v| alive += @popCount(v);
    var buf: [128]u8 = undefined;
    const line = try std.fmt.bufPrint(&buf, "alive={d} sim_ms={d:.3}\n", .{ alive, ms });
    try std.Io.File.stdout().writeStreamingAll(io, line);
}
