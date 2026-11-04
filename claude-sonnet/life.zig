const std = @import("std");

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    const gpa = init.gpa;
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    const n: usize = try std.fmt.parseInt(usize, args[1], 10);
    const gens: usize = try std.fmt.parseInt(usize, args[2], 10);
    const buf = try std.Io.Dir.cwd().readFileAlloc(io, args[3], gpa, .unlimited);
    defer gpa.free(buf);

    const w: usize = (n + 63) / 64;
    const l: u6 = @intCast(n - 64 * (w - 1) - 1); // valid bits in last word minus one
    const lm: u64 = if (l == 63) ~@as(u64, 0) else (@as(u64, 1) << (l + 1)) - 1;
    const sz = n * w;
    var cur = try gpa.alloc(u64, sz);
    var nxt = try gpa.alloc(u64, sz);
    const we = try gpa.alloc(u64, sz);
    const ee = try gpa.alloc(u64, sz);
    @memset(cur, 0);
    @memset(nxt, 0);

    var k: usize = 0;
    for (buf) |c| {
        if (k >= n * n) break;
        if (c == '1') {
            const r = k / n;
            const q = k % n;
            cur[r * w + q / 64] |= @as(u64, 1) << @intCast(q % 64);
            k += 1;
        } else if (c == '0') {
            k += 1;
        }
    }

    const t0 = std.Io.Clock.awake.now(io);
    var g: usize = 0;
    while (g < gens) : (g += 1) {
        var r: usize = 0;
        while (r < n) : (r += 1) {
            const row = cur[r * w .. (r + 1) * w];
            const wr = we[r * w .. (r + 1) * w];
            const er = ee[r * w .. (r + 1) * w];
            var i: usize = 0;
            while (i < w) : (i += 1) {
                const x = row[i];
                const e = if (i < w - 1)
                    (x >> 1) | (row[i + 1] << 63)
                else
                    (x >> 1) | ((row[0] & 1) << l);
                var wv = if (i > 0)
                    (x << 1) | (row[i - 1] >> 63)
                else
                    (x << 1) | ((row[w - 1] >> l) & 1);
                if (i == w - 1) wv &= lm;
                wr[i] = wv;
                er[i] = e;
            }
        }
        r = 0;
        while (r < n) : (r += 1) {
            const ru = (if (r == 0) n - 1 else r - 1) * w;
            const rd = (if (r == n - 1) 0 else r + 1) * w;
            const rm = r * w;
            const uw = we[ru .. ru + w];
            const ue = ee[ru .. ru + w];
            const uc = cur[ru .. ru + w];
            const mw = we[rm .. rm + w];
            const me = ee[rm .. rm + w];
            const mc = cur[rm .. rm + w];
            const dw = we[rd .. rd + w];
            const de = ee[rd .. rd + w];
            const dc = cur[rd .. rd + w];
            const o = nxt[rm .. rm + w];
            var i: usize = 0;
            while (i < w) : (i += 1) {
                var a = uw[i];
                var b = uc[i];
                var c = ue[i];
                const s1 = a ^ b ^ c;
                const c1 = (a & b) | (c & (a ^ b));
                const d = mw[i];
                const e = me[i];
                const s2 = d ^ e;
                const c2 = d & e;
                a = dw[i];
                b = dc[i];
                c = de[i];
                const s3 = a ^ b ^ c;
                const c3 = (a & b) | (c & (a ^ b));
                const on = s1 ^ s2 ^ s3;
                const k1 = (s1 & s2) | (s3 & (s1 ^ s2));
                const par = c1 ^ c2 ^ c3 ^ k1;
                const two = (c1 & c2) | (c3 & k1) | ((c1 | c2) & (c3 | k1));
                o[i] = par & ~two & (on | mc[i]);
            }
        }
        const t = cur;
        cur = nxt;
        nxt = t;
    }
    const t1 = std.Io.Clock.awake.now(io);
    const ns: i96 = t0.durationTo(t1).nanoseconds;
    const ms: f64 = @as(f64, @floatFromInt(ns)) / 1e6;

    var alive: u64 = 0;
    for (cur) |x| alive += @popCount(x);

    var obuf: [128]u8 = undefined;
    var fw = std.Io.File.stdout().writerStreaming(io, &obuf);
    try fw.interface.print("alive={d} sim_ms={d:.3}\n", .{ alive, ms });
    try fw.interface.flush();
}
