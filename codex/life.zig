const std = @import("std");

fn halo(a: []u8, n: usize, s: usize) void {
    var i: usize = 1;
    while (i <= n) : (i += 1) {
        const r = i * s;
        a[r] = a[r + n];
        a[r + n + 1] = a[r + 1];
    }
    var j: usize = 0;
    while (j < s) : (j += 1) {
        a[j] = a[n * s + j];
        a[(n + 1) * s + j] = a[s + j];
    }
}

fn step(a: []const u8, b: []u8, n: usize, s: usize) u64 {
    const V = @Vector(16, u8);
    const zero: V = @splat(0);
    const one: V = @splat(1);
    const two: V = @splat(2);
    const three: V = @splat(3);
    var live: u64 = 0;
    var i: usize = 1;
    while (i <= n) : (i += 1) {
        var j: usize = 1;
        var k = i * s + 1;
        while (j + 15 <= n) : ({ j += 16; k += 16; }) {
            const nw: V = @as(*align(1) const V, @ptrCast(a.ptr + k - s - 1)).*;
            const nn: V = @as(*align(1) const V, @ptrCast(a.ptr + k - s)).*;
            const ne: V = @as(*align(1) const V, @ptrCast(a.ptr + k - s + 1)).*;
            const ww: V = @as(*align(1) const V, @ptrCast(a.ptr + k - 1)).*;
            const ee: V = @as(*align(1) const V, @ptrCast(a.ptr + k + 1)).*;
            const sw: V = @as(*align(1) const V, @ptrCast(a.ptr + k + s - 1)).*;
            const ss: V = @as(*align(1) const V, @ptrCast(a.ptr + k + s)).*;
            const se: V = @as(*align(1) const V, @ptrCast(a.ptr + k + s + 1)).*;
            const x = nw + nn + ne + ww + ee + sw + ss + se;
            const cur: V = @as(*align(1) const V, @ptrCast(a.ptr + k)).*;
            const v = @select(u8, x == three, one, @select(u8, x == two, cur, zero));
            @as(*align(1) V, @ptrCast(b.ptr + k)).* = v;
            live += @reduce(.Add, v);
        }
        while (j <= n) : ({ j += 1; k += 1; }) {
            const x = a[k - s - 1] + a[k - s] + a[k - s + 1] + a[k - 1] + a[k + 1] + a[k + s - 1] + a[k + s] + a[k + s + 1];
            const v: u8 = @intFromBool(x == 3) | (@intFromBool(x == 2) & a[k]);
            b[k] = v;
            live += v;
        }
    }
    return live;
}

pub fn main(init: std.process.Init) !void {
    var it = std.process.Args.Iterator.init(init.minimal.args); defer it.deinit(); _ = it.next();
    const ns = it.next() orelse return; const gs = it.next() orelse return; const name = it.next() orelse return;
    const n = try std.fmt.parseInt(usize, ns, 10); const gens = try std.fmt.parseInt(usize, gs, 10);
    if (n == 0) return;
    const s = n + 2;
    const alloc = init.gpa;
    var a = try alloc.alloc(u8, s * s); defer alloc.free(a);
    var b = try alloc.alloc(u8, s * s); defer alloc.free(b);
    @memset(a, 0); @memset(b, 0);
    const input = try std.Io.Dir.cwd().readFileAlloc(init.io, name, alloc, .limited(std.math.maxInt(usize))); defer alloc.free(input);
    var q: usize = 0; var i: usize = 1;
    while (i <= n) : (i += 1) { var j: usize = 1; while (j <= n) : (j += 1) {
        while (input[q] == '\n' or input[q] == '\r') : (q += 1) {}
        a[i*s+j] = @intFromBool(input[q] == '1'); q += 1;
    } }
    const start = std.Io.Clock.Timestamp.now(init.io, .awake); var live: u64 = 0;
    if (gens == 0) { i = 1; while (i <= n) : (i += 1) { var j: usize = 1; while (j <= n) : (j += 1) live += a[i*s+j]; } }
    var g: usize = 0;
    while (g < gens) : (g += 1) { halo(a, n, s); live = step(a, b, n, s); std.mem.swap([]u8, &a, &b); }
    const elapsed: f64 = @as(f64, @floatFromInt(start.untilNow(init.io).raw.toNanoseconds())) / 1_000_000.0;
    var out_buffer: [128]u8 = undefined;
    var out_writer = std.Io.File.stdout().writer(init.io, &out_buffer);
    const out = &out_writer.interface;
    try out.print("alive={d} sim_ms={d:.3}\n", .{live, elapsed}); try out.flush();
}
