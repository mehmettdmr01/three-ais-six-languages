// Same as fast.zig, but with explicit vectors (@Vector): 16 cells per step. Zig 0.17 (official and
// Homebrew builds, ReleaseFast) did not vectorize the plain loop in fast.zig; checked in the disassembly.
const std = @import("std");

inline fn rule(c: u8, m: u8) u8 {
    return @as(u8, @intFromBool(c == 3)) | (@as(u8, @intFromBool(c == 2)) & m);
}

fn step(n: usize, cur: []const u8, next: []u8) void {
    for (0..n) |y| {
        const u = cur[(if (y == 0) n - 1 else y - 1) * n ..][0..n];
        const m = cur[y * n ..][0..n];
        const d = cur[(if (y == n - 1) 0 else y + 1) * n ..][0..n];
        const o = next[y * n ..][0..n];
        const V = @Vector(16, u8);
        var x: usize = 1;
        while (x + 16 <= n - 1) : (x += 16) {
            const load = struct {
                fn f(s: []const u8, i: usize) V {
                    return s[i..][0..16].*;
                }
            }.f;
            const c = load(u, x - 1) + load(u, x) + load(u, x + 1) + load(m, x - 1) + load(m, x + 1) + load(d, x - 1) + load(d, x) + load(d, x + 1);
            const three: V = @splat(3);
            const two: V = @splat(2);
            const one: V = @splat(1);
            const zero: V = @splat(0);
            const is3 = @select(u8, c == three, one, zero);
            const is2 = @select(u8, c == two, load(m, x), zero);
            o[x..][0..16].* = is3 | is2;
        }
        while (x < n - 1) : (x += 1) {
            o[x] = rule(u[x - 1] + u[x] + u[x + 1] + m[x - 1] + m[x + 1] + d[x - 1] + d[x] + d[x + 1], m[x]);
        }
        o[0] = rule(u[n - 1] + u[0] + u[1] + m[n - 1] + m[1] + d[n - 1] + d[0] + d[1], m[0]);
        o[n - 1] = rule(u[n - 2] + u[n - 1] + u[0] + m[n - 2] + m[0] + d[n - 2] + d[n - 1] + d[0], m[n - 1]);
    }
}

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const args = try init.minimal.args.toSlice(arena);
    const n = try std.fmt.parseInt(usize, args[1], 10);
    const gens = try std.fmt.parseInt(usize, args[2], 10);
    const text = try std.Io.Dir.cwd().readFileAlloc(init.io, args[3], arena, .unlimited);
    var cur = try arena.alloc(u8, n * n);
    var next = try arena.alloc(u8, n * n);
    var i: usize = 0;
    for (text) |b| {
        if (b != '\n') {
            cur[i] = @intFromBool(b == '1');
            i += 1;
        }
    }
    const t0 = std.Io.Clock.awake.now(init.io);
    for (0..gens) |_| {
        step(n, cur, next);
        std.mem.swap([]u8, &cur, &next);
    }
    const t1 = std.Io.Clock.awake.now(init.io);
    const sim_ms = @as(f64, @floatFromInt(t0.durationTo(t1).toNanoseconds())) / 1e6;
    var alive: u64 = 0;
    for (cur) |b| alive += b;
    var buf: [64]u8 = undefined;
    var w: std.Io.File.Writer = .init(.stdout(), init.io, &buf);
    try w.interface.print("alive={d} sim_ms={d:.3}\n", .{ alive, sim_ms });
    try w.interface.flush();
}
